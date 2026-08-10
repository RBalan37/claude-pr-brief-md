# AMVP-156149 — Batch device grouping for playbook runs without loading the full inventory

## Problem

Today, when a researcher starts a playbook run against a device list, the writer loads
every device record from the inventory service before it can apply grouping rules. That
works for small lists but breaks down above a few thousand devices: `playbook_dao.py:88`
loads the full result set into memory, and `device_grouper.py:41` then walks the entire
collection synchronously on the request thread. Runs time out, and the API returns 504s
even though the grouping logic itself is cheap.

## Fix

This change introduces a streaming grouper that reads devices in pages, applies grouping
rules incrementally, and writes group membership rows as it goes. The playbook run still
returns the same group structure to callers, but the heavy lifting moves off the request
path into a background job once the list exceeds a configurable threshold.

## Device paging and incremental grouping

The new `PagedDeviceReader` in `device_grouper.py:21` fetches inventory in chunks of 500
via the existing inventory client. Each page is passed to `GroupAccumulator.add_page`
at `device_grouper.py:64`, which maintains running counts and membership without
retaining full device objects after a page is processed. That keeps memory flat regardless
of list size.

## Async handoff for large lists

When the selected device count exceeds the threshold defined at `playbook_service.py:112`
(default 2,000), the API enqueues a grouping job instead of running inline. The job
handler at `jobs/group_devices.py:18` reuses the same `PagedDeviceReader` and writes
progress to `playbook_run_groups` through `playbook_dao.py:24`. The HTTP handler returns
202 with a run id; clients poll the existing run-status endpoint, which already knows how
to surface in-progress states.

## Key design, and it is deliberately not the design of playbook

The obvious alternative was to extend the existing playbook template model so grouping
rules live inside each playbook step. That would reuse the DSL authors already know, but
it couples inventory paging to the step executor and makes every playbook run pay the
cost of loading step metadata even when grouping is the only heavy part. Instead, grouping
is a pre-run concern: `playbook_service.py:97` calls the grouper before steps execute,
and playbooks stay unchanged. The rejected path would also have required migrating every
playbook that references device groups, which this approach avoids entirely.

## Open decisions

Multi-tenancy for the new `playbook_run_groups` table is on standby. Diogo is deciding
whether tenant id belongs on the row or is inferred from the parent run. Until that is
settled, the migration adds a nullable `tenant_id` column and the DAO does not filter on
it yet.

## Data / control flow

The user selects devices in the UI and starts a run. The API receives the device id list
at `playbook_api.py:203`, counts it, and either groups inline or enqueues a job. The
grouper pages inventory, accumulates groups, and persists rows through the DAO. When
complete, the playbook executor loads group ids from `playbook_dao.py:51` and proceeds
with the existing step runner unchanged.

## Blast radius

This touches the playbook start path, the inventory client call pattern, and a new DB
table. Existing playbooks and step definitions are unchanged. The main risk is the async
branch: any client that assumes grouping always completes synchronously will see 202
instead of 200 for large lists (~15% of production runs per last month's metrics). The
inventory service will see more frequent, smaller requests instead of occasional huge
ones; total volume stays similar but peak concurrency rises. Reviewers should focus on
`playbook_service.py:97-140` (sync/async split), `jobs/group_devices.py` (retry and
failure handling), and the migration rollback story.
