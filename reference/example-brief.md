# AMVP-158214 + AMVP-158302 — Trigger the AMS→RMS device sync from a scheduler, split across 2 PRs

**TLDR**: The data path that pulls devices from AMS and upserts them into the RMS `device` table already exists end to end. What's missing is the trigger. This work adds a `DEVICE_SYNC` scheduler type so the existing RMS cron picks up a user's ASQ-based onboarding job and runs the sync on a schedule (e.g. every 8h). Split into 2 atomic PRs: PR 1 wires the trigger, PR 2 adds the creation endpoint.

**Stacked on AMVP-158213** — this reuses `ams_query_service.get_devices`, which only exists on the `rodrigo.balan.AMVP-158213-endpoint-to-get-device` branch, not master. PR 1 branches off that branch. Merge order: 158213 → PR 1 (158214) → PR 2 (158302).

---

## Problem

The ticket says: user clicks submit → get devices for those filters → check the internal table → add the ones that aren't there. When I traced this against the code, almost all of the *data path* already exists on the AMVP-158213 branch:

- Retrieval: `device_sync_service.run(tenant_id, tenant_name, asq)` streams devices via `tenant_api_dao.stream_devices` → `ams_query_service.get_devices` (the shared logic from AMVP-158213).
- "Check if there, add if not": `device_dao.upsert` uses `INSERT ... ON CONFLICT (tenant_id, device_id) DO UPDATE` — already idempotent, so new devices are inserted and existing ones refreshed in one statement.

The real gap is that **nothing triggers `rms_device_sync_job`**. Its entry point `job.py` only runs when handed a `RunDeviceSyncRequest` flag manually, and the RMS scheduler cron (`rms_credential_rotation_scheduler_job/src/main.py`) only knows how to trigger entity-based `CHANGE_PASSWORD` rotations. `JobType` has a single value, `CHANGE_PASSWORD` (`rms_lib/enums/job_type.py`).

---

## Overall approach

Add `DEVICE_SYNC` as a second `JobType` and let the existing scheduler cron dispatch it. A `DEVICE_SYNC` scheduler carries the ASQ filter and `tenant_name` in its `configs` JSONB and, unlike a rotation scheduler, has **no `entity_ids`** — the whole point is to discover devices, not operate on a known list. Everything downstream (`device_sync_service.run`, `stream_devices`, `upsert`) is reused as-is.

## PR breakdown

| PR | Story | What it builds | Files it would touch | Why this order |
|----|-------|----------------|----------------------|----------------|
| PR 1 | AMVP-158214 | Backend trigger: `JobType.DEVICE_SYNC`, K8s dispatch helper, `_trigger_schedule` branch, a `Job` row per trigger | `rms_lib/enums/job_type.py`, `rms_credential_rotation_scheduler_job/src/main.py`, a K8s dispatch helper | Adds capability that isn't acionable yet — safe to merge alone |
| PR 2 | AMVP-158302 | Creation endpoint: create a `Scheduler` with `job_type=device_sync`, ASQ + `tenant_name` in `configs`, crontab in `trigger`, ASQ validated on create | `rms_app_service` route + schema + service, `scheduler_dao.create_scheduler` | Only makes sense once the cron can process these schedulers |

**Atomicity:** after PR 1, master is consistent — the cron can process `DEVICE_SYNC` schedulers, but nothing creates them yet, so there is zero production impact. PR 2 makes it acionable, at which point the flow is complete end to end.

---

## Key design, and why not X

**Reuse the `Scheduler` model with a new `job_type`, not a new sync-config table.**
The `Scheduler` model already has everything needed: `trigger` (CRON/ONCE), `configs` JSONB, `status`, `last_triggered_at`, and the cron loop in `main.py:run` already reads active schedulers and evaluates `should_trigger`. A dedicated device-sync table would duplicate all of that scheduling machinery. The one wrinkle is that the current `_trigger_schedule` bails when `entity_ids` is empty (`main.py`, the "has no entity_ids" warning). DEVICE_SYNC legitimately has no entity_ids, so the branch must skip that guard rather than treat empty as an error.

**Dispatch a K8s job, not run the sync inline in the scheduler process.**
The scheduler cron is a short-lived job that fans out over many tenants with `asyncio.gather`. Running a full AMS pull (potentially tens of thousands of devices, paginated 1000 at a time) inline would block the whole cron pass. Dispatching `rms_device_sync_job` as its own K8s job is exactly what `group_processor` already does for the researcher and runner jobs (`group_processor._trigger_k8s_job`, `group_processor.py:311`), and it isolates each tenant's sync. This is the "job triggering a job" pattern.

**Two-layer cadence — reuse it, don't add a second poller.**
The cadence works in two layers, and the periodic "check AMS for new/updated devices" behaviour falls out of it for free:
- Layer 1, the poller: `rms_credential_rotation_scheduler_job` already runs every 5 minutes (`scheduler_trigger._WINDOW_SECONDS = 5 * 60`), reads all active schedulers, and evaluates `should_trigger` for each.
- Layer 2, each scheduler's own CRON: a device-sync scheduler stores a crontab like `0 */8 * * *` in `trigger`. The 5-minute poller checks whether that 8h schedule is due within the next window and only dispatches the sync when the 8h mark arrives (`scheduler_trigger.py` CRON branch).

So the "every 8h re-sync from AMS" is just a device-sync `Scheduler` with an 8h crontab. No new cron, no new poller — the same 5-minute loop that drives rotations drives this.

---

## Data / control flow

```
PR 2: user submits onboarding job (ASQ + schedule)
  → validate ASQ (ams_query_service.get_parameters), read tenant_name from X-ARMIS-TENANT-NAME
  → create Scheduler { job_type: device_sync, trigger: { cron }, configs: { asq, tenant_name } }

PR 1: rms_credential_rotation_scheduler_job (cron, every 5 min)
  → get_active_schedulers → should_trigger? (evaluates each scheduler's crontab)
  → _trigger_schedule:
       job_type == device_sync?
         → write one Job row (observability)
         → build RunDeviceSyncRequest(tenant_id, tenant_name, asq from configs)
         → dispatch rms_device_sync_job K8s job   (group_processor._trigger_k8s_job pattern)
       else (change_password) → existing entity_ids / orchestrate_devices path (unchanged)

existing: rms_device_sync_job (K8s)
  → device_sync_service.run → stream_devices → ams_query_service.get_devices (AMS, paginated)
  → device_dao.upsert  (INSERT ... ON CONFLICT → add new, refresh existing)
```
---

## Anticipated impact

**Production impact: Medium (PR 1), Low (PR 2).** PR 1 touches the live scheduler cron (`rms_credential_rotation_scheduler_job`), which currently drives credential rotations. The change is additive (a new branch keyed on `job_type`) and the `CHANGE_PASSWORD` path stays byte-for-byte the same, but any regression in `_trigger_schedule` would affect rotations too, so the branching must be carefully isolated and tested. PR 2 is a new creation endpoint plus validation — it doesn't change existing behaviour. The sync job itself and `upsert` are unchanged throughout, so the retrieval/write risk is low.

**Development impact: Low to Medium.** No DB migration: `Scheduler.configs` is already JSONB and `job_type` is stored as `Text` (per `scheduler.py`), so a new value needs no schema change. The work is concentrated in one function in the scheduler cron plus a small K8s dispatch helper and the enum (PR 1), and a route/schema/service for creation (PR 2).
