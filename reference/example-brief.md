# AMVP-156149 — Store what we know about a device class, instead of re-deriving it every run

**TLDR:** I want to add a small persistent cache (`device_class_knowledge`) so the
writer stops re-grouping and re-searching a device class from scratch on every run.
Main things I want your take on: the TTL value, and whether the first write on a
cache miss should be synchronous or queued.

**Problem:** Today, whenever the writer needs to describe a device class (say, "smart
thermostats"), it re-derives everything from scratch on every single run: it re-groups
the raw device list in `device_grouper.py:21`, re-runs a web search for the category
in `web_search.py:64-74`, and re-asks the model to summarize what it found. This is
slow (the search alone adds 8-12s per class, per the timing logged around
`web_search.py:64`), it's non-deterministic across runs, and it throws away work
we've already paid for. There is no persistent notion of "what we know about smart
thermostats" today — only a transient, per-run one.

**Proposed approach:** Introduce a `device_class_knowledge` table that stores a
durable, versioned summary per device class, keyed on a normalized class name. The
grouper and writer would both read from this table first and only fall back to the
existing live-derivation path (grouping + search + summarize) on a cache miss, at
which point they'd write the result back. A device class's knowledge would refresh on
a TTL, not on every run. Nothing in `device_grouper.py:21` or `web_search.py:64-74`
would change — only what happens before and after them.

## Storage shape, and why not just cache the search result

My first instinct was to slap a cache in front of `web_search.py:64-74` and call it
done. I'd set that aside: the search result isn't the thing we actually want to
remember. What matters is the *distilled* knowledge — the summary the model produces
after grouping and searching — not the raw search payload, which is noisy, sometimes
empty (see `web_search.py:64-74`, which already turns a failed search into a default
placeholder string and continues), and not reusable by the pipeline's other consumers
(the writer needs the summary, not the search JSON). So instead I'd add a new table
storing the finished summary plus the inputs that produced it (device list hash,
search query, model version), so a cache hit is a guarantee of *equivalent output*,
not just equivalent search.

## Key design, and why not model it like a playbook

`playbook_dao.py` already has a pattern for durable, versioned content: a playbook is
written once and referenced by ID everywhere downstream (`playbook_dao.py:24`). The
obvious move would be to model device class knowledge the same way — write it once,
hand callers an ID. I'm proposing against that. Playbooks are authored and reviewed
by a human before they're relied on; device class knowledge is machine-derived and
needs to self-heal when it goes stale (a device class's public information changes —
new certifications, a product recall, a firmware naming change) without a human in
the loop. So instead of an immutable ID handed around, I'd look `device_class_knowledge`
up by class name on every call, with the TTL check happening inside that lookup, not
as a separate cron job. The tradeoff is an extra lookup per call versus playbook's
zero-cost ID reference — I think that's worth it against the complexity of a
background refresh job, but open to arguing the other way if you disagree.

## Grouping stays untouched, only its output would get cached

`device_grouper.py:21` would keep grouping raw devices into classes exactly as today
— this proposal doesn't touch the grouping logic itself, only what happens after: the
grouped class name becomes the cache key, and the grouper would check the table
before deciding to kick off a search.

## Open questions for reviewers

- **What should the TTL be?** I'd start with 7 days as a placeholder, but I don't have
  a strong basis for that number. Does 7 days sound right for how often device class
  info actually changes, or should this be configurable per class from the start?
- **Synchronous or queued write-back on a cache miss?** Writing back synchronously is
  simplest, but it means the caller who hits the miss eats the full 8-12s. Should the
  first write instead go through a queue so no single caller pays for it? I don't have
  a strong opinion here — wanted your read before I commit to one.
- **Is a 7-day-stale description ever actually dangerous?** For most classes this is
  invisible, but for one that just had a real-world change (a recall, a rebrand)
  there's a window where we'd confidently report outdated info. Worth a shorter TTL
  for specific categories, or is this an acceptable tradeoff everywhere?

## Data flow (proposed)

The writer would ask the grouper for a class's knowledge. The grouper normalizes the
class name and checks `device_class_knowledge`. On a hit within TTL, it returns the
stored summary directly to the writer. On a miss or stale hit, it falls through to
the existing path: group the raw devices (`device_grouper.py:21`), run the web search
(`web_search.py:64-74`), summarize, write the result back to the table, then return it
to the writer. The writer's interface wouldn't change either way — it always gets a
summary string back, never a cache-hit flag.

## Anticipated impact

**Production impact level: Low.** This sits behind the existing grouper/writer
interfaces — no caller-facing contract changes, and the fallback path is the exact
code that runs today, so a bug in the new caching layer degrades to today's behaviour
rather than breaking anything new. The risk that exists is entirely in staleness (see
open questions above), not in availability.

**Development impact level: Low.** One new table, one new write path. The only other
consumer I know of today is the writer; a second consumer (the digest email job) is
planned for next quarter and would get caching for free once this lands.

I'd plan this as a single PR — the table, the read-through/write-back logic in the
grouper, and tests for the TTL boundary — rather than splitting it, since it's small
enough to review as one unit. Let me know if you'd rather see it split differently.
