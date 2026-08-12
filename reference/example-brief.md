# AMVP-156149 — Store what we know about a device class, instead of re-deriving it every run

**Problem:** Today, whenever the writer needs to describe a device class (say, "smart
thermostats"), it re-derives everything from scratch on every single run: it re-groups
the raw device list in `device_grouper.py:21`, re-runs a web search for the category
in `web_search.py:64-74`, and re-asks the model to summarize what it found. This is
slow (the search alone adds 8-12s per class), it's non-deterministic (two runs on the
same class can disagree on details), and it throws away work the team has already
paid for. There is no persistent notion of "what we know about smart thermostats" —
only a transient, per-run one.

**Fix:** Introduce a `device_class_knowledge` table that stores a durable, versioned
summary per device class, keyed on a normalized class name. The grouper and writer
both read from this table first and only fall back to the old live-derivation path
(grouping + search + summarize) on a cache miss, at which point they write the result
back. A device class's knowledge is refreshed on a TTL, not on every run.

## Storage shape, and why not just cache the search result

The obvious first instinct is to slap a cache in front of `web_search.py:64-74` and
call it done. That was rejected: the search result is not the thing we actually want
to remember. What matters is the *distilled* knowledge — the summary the model
produces after grouping and searching — not the raw search payload, which is noisy,
sometimes empty (see `web_search.py:64-74`, which turns a failed search into a
default placeholder string and continues), and not reusable across the pipeline's
other consumers (the writer needs the summary, not the search JSON). The new table,
defined in `playbook_dao.py:24`, stores the finished summary plus the inputs that
produced it (device list hash, search query, model version), so a cache hit is a
guarantee of *equivalent output*, not just *equivalent search*.

## Key design, and it is deliberately not the design of playbook

`playbook_dao.py` already has a pattern for durable, versioned content: a playbook is
written once and referenced by ID everywhere downstream (`playbook_dao.py:24`). The
natural move would have been to model device class knowledge the same way — write it
once, hand callers an ID. That was rejected here. Playbooks are authored and reviewed
by a human before they're relied on; device class knowledge is machine-derived and
needs to self-heal when it goes stale (a device class's public information changes —
new certifications, a product recall, a firmware naming change) without a human in
the loop. So instead of an immutable ID handed around, `device_class_knowledge` is
looked up by class name on every call, and the TTL check happens inside that lookup
(`playbook_dao.py:24`), not as a separate cron job. The tradeoff is an extra lookup
per call versus playbook's zero-cost ID reference; that cost is a single indexed
read and was judged acceptable against the complexity of a background refresh job.

## Grouping is unchanged, only its output is now cached

`device_grouper.py:21` groups raw devices into classes exactly as before — this PR
does not touch the grouping logic itself, only what happens after: the grouped class
name becomes the cache key, and the grouper now checks the table before deciding to
kick off a search.

## Open decisions

- **TTL value is not settled.** The table (`playbook_dao.py:24`) has a
  `refreshed_at` column but the PR ships with a 7-day TTL as a placeholder. Tenancy
  of this decision is on standby — Diogo owns the final number and it may end up
  configurable per class rather than global.
- **Cold-start behaviour for brand-new classes** (never seen before) is unchanged
  from today: full live derivation, no shortcuts. Whether that first result should be
  written back synchronously or queued is still open; this PR writes it back
  synchronously, which is simplest but adds the full 8-12s to that one caller.

## Data flow

The writer asks the grouper for a class's knowledge. The grouper normalizes the class
name and checks `device_class_knowledge` (`playbook_dao.py:24`). On a hit within TTL,
it returns the stored summary directly to the writer. On a miss or stale hit, it falls
through to the existing path: group the raw devices (`device_grouper.py:21`), run the
web search (`web_search.py:64-74`), summarize, write the result back to the table, and
then return it to the writer. The writer's interface does not change either way — it
always receives a summary string, never a cache-hit flag.

## Blast radius

This touches every caller of the grouper's class-summary method, which today is just
the writer, but a second consumer (the digest email job) is planned for next quarter
and will get caching for free. Existing behaviour changes in one way a reviewer
should notice: a device class's description can now be up to 7 days stale, where
before it was always freshly derived. For most classes this is invisible, but for a
class that just had a real-world change (a recall, a rebrand) there's a window where
the pipeline will confidently report outdated information. The write path adds one
new table and one new write per cache miss; read volume on the table scales with
writer calls, currently a few hundred a day, so no scale concern there. Risk is
concentrated in the TTL choice above, not in the code.
