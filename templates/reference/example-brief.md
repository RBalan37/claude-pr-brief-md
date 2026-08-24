# ACC-214 + ACC-215 — Soft-delete user accounts with a 30-day recovery window, split across 2 PRs

**TLDR**: Account deletion today issues a hard `DELETE` that cascades through orders, sessions, and the audit log with no way back. This work replaces it with a `deleted_at` soft-delete: PR 1 adds the column, revokes the user's active sessions, and flips every read path to filter deleted rows by default. PR 2 adds a restore endpoint and a scheduled cleanup that hard-deletes rows once the 30-day window passes.

**Stacked on ACC-213** — PR 1 reuses `session_dao.revoke_all_for_user`, which only exists on the `feature/ACC-213-bulk-session-revoke` branch, not master. PR 1 branches off that branch. Merge order: 213 → PR 1 (214) → PR 2 (215).

---

## Problem

The ticket says: deleting an account should stop the user from logging in and hide them from admin views, with a 30-day undo window. Tracing this against the code, `account_service.delete_account` (`account_service.py:88`) calls `user_dao.hard_delete(user_id)`, which issues `DELETE FROM users WHERE id = ?` and relies on `ON DELETE CASCADE` foreign keys on `orders`, `sessions`, and `audit_log` (`schema/001_initial.sql:40-52`) to clean up related rows. There is no undo path today — once the cascade runs, the data is gone.

The real gap isn't "add a delete flow" — a delete flow already exists and works. It's that the existing one is irreversible, and every place that reads a user (`user_dao.get`/`list`, the admin view, billing lookups — about a dozen call sites) needs to agree on what "deleted" means before a restore window is even meaningful.

---

## Overall approach

Add a nullable, indexed `deleted_at` timestamp to `users` instead of physically removing the row. `user_dao.delete` sets `deleted_at = now()` and revokes the user's sessions instead of issuing a `DELETE`; `orders` and `audit_log` are untouched by the cascade going forward. Every read path defaults to `WHERE deleted_at IS NULL`, with an explicit `include_deleted=True` escape hatch for the two admin views that need it. Restoring just nulls the column back out. The flow spans both PRs, so it's worth spelling out end to end:

```
DELETE /accounts/:id
  → account_service.delete_account(user_id)
  → session_dao.revoke_all_for_user(user_id)        (from ACC-213)
  → user_dao.delete(user_id) → UPDATE users SET deleted_at = now() WHERE id = ?
  (orders / audit_log rows untouched — cascade no longer fires)

any read (user_dao.get / list, admin view, billing lookup)
  → default WHERE deleted_at IS NULL   (include_deleted=True opts in)

POST /accounts/:id/restore                          (PR 2)
  → user_dao.restore(user_id) → UPDATE users SET deleted_at = NULL WHERE id = ?

daily cleanup job                                    (PR 2)
  → SELECT id FROM users WHERE deleted_at < now() - interval '30 days'
  → user_dao.hard_delete(user_id)   (the original DELETE, now only reached after the window)
```

## PR breakdown

| PR | Story | What it builds | Files it would touch | Why this order |
|----|-------|----------------|----------------------|----------------|
| PR 1 | ACC-214 | `deleted_at` migration, `user_dao.delete`/`get`/`list` updated to soft-delete + default-filter, session revocation on delete | `schema/migrations/`, `user_dao.py`, `account_service.py` | Makes delete reversible in the DB immediately — safe on its own, no restore UI needed yet |
| PR 2 | ACC-215 | `POST /accounts/:id/restore`, a daily cleanup job that hard-deletes rows past the 30-day window | account routes, `account_service.py`, a scheduled cleanup job | Only useful once PR 1's column and filtering exist |

**Atomicity:** after PR 1, a deleted user disappears from every existing read path exactly as before — no observable regression — but nothing can undo it except a manual `UPDATE`. PR 2 adds the actual recovery path and closes the retention loop.

---

## Key design, and why not X

**Add a `deleted_at` column, not a separate tombstone table.**
A tombstone table would mean every one of the roughly dozen call sites that reads a user — `user_dao.py`, `admin/users_view.py`, `billing/invoice_service.py` — has to also anti-join against it, doubling the complexity of every existing query. A nullable column is one predicate those queries already need to add once, and it survives joins for free.

**Filter at the DAO layer by default, not leave it to each caller.**
The alternative — trust every call site to remember `WHERE deleted_at IS NULL` — is exactly the kind of thing that gets missed once and becomes a real bug: a "deleted" user's orders or profile staying visible somewhere. Centralizing the default in `user_dao.get`/`list` means a caller has to opt in to see deleted rows, not opt out.

**Hard-delete on a 30-day delay, not immediately and not indefinitely.**
Immediate hard-delete defeats the point of a recovery window; keeping rows forever conflicts with the data-retention policy already applied to closed accounts elsewhere (`compliance/retention_policy.md`). A daily cleanup job that hard-deletes anything past the cutoff reuses the existing `user_dao.hard_delete` path — it just runs later, on a smaller, already-soft-deleted set.

**Revoke sessions on delete, don't wait for tokens to expire.**
A soft-deleted user's existing session tokens would otherwise keep working until they naturally expire (up to 24h). Reusing `session_dao.revoke_all_for_user` from ACC-213 closes that window immediately rather than adding a second, bespoke revocation path.

---

## Anticipated impact

**Production impact: Medium.** Every existing read path must respect the new default filter or a "deleted" user's data could leak back into results — the DAO-layer default (see Key design) is what contains that risk to one change point instead of a sweep across a dozen call sites. The write path itself (soft-delete instead of hard-delete) is strictly less destructive than what runs today.

**Development impact: Low to Medium.** One migration, the DAO changes, and verifying the dozen call sites still filter correctly. PR 2 is additive — a new endpoint and a new scheduled job — with no changes to existing behavior.

**Deployment impact: the `deleted_at` migration must run before PR 1's code deploys** — the DAO's default filter references the column and would fail against a `users` table that doesn't have it yet.
