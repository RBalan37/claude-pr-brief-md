---
name: pr-brief
description: Produce a short, direct design brief for a story or ticket — wherever it lives (Jira, GitHub Issues/Projects, Linear, Asana, ClickUp, Notion, or just pasted text) — written BEFORE the code change exists. A plain-language document that lays out the problem, the proposed approach, a handful of key design calls (each a stated decision with the alternative you set aside, not a question), and the anticipated impact across production, development, and deployment. Grounded in the current codebase (file:line where it genuinely helps) — where the change would land and what patterns already exist there — not in a diff, because there isn't one yet. Adapts to a single fix/feature, work too big for one atomic PR (split across several, regardless of tracker labels), or a broader initiative. Writes a markdown file and, only when a flow or split is genuinely clearer as a picture than a paragraph, renders one too. Use right after a story exists, when asked to "brief", "write up", "plan out", or "structure my thoughts on" a feature or fix before implementation starts. Tracker-agnostic by design so a whole team can share it. NOT a code review and NOT a description of a finished change.
allowed-tools: Bash, Read, Write, Grep, Glob, WebFetch, mcp__atlassian__*, mcp__linear__*, mcp__asana__*, mcp__notion__*, mcp__github__*
argument-hint: "[ticket ID or URL | nothing = describe the story to me]"
---

# PR Brief → pre-implementation design brief for reviewers

Generate a **brief**: the document you send reviewers *before you write the code*,
right after the story exists, so they can react to the plan — agree with it, push
back on it, or suggest a different shape — while it's still cheap to change. It is
not a report of what you built; there is nothing built yet. It is a proposal,
grounded in the real codebase as it stands today, concise enough that a reviewer can
form an opinion in a couple of minutes.

**Keep it short.** The gold-standard example is `reference/example-brief.md` — read
it before you start. It runs 4-6 titled sections total (Problem, Overall approach,
optionally a PR breakdown table, one "Key design, and why not X" section holding
several bolded points, Anticipated impact). Inside each section, write direct,
unambiguous prose — do not fragment one section into a header per sub-point. Not
every claim needs a `file:line`; cite code where it genuinely grounds a claim, not
as a formality. Reviewers respond to Key design, not diagrams — so a diagram is
never its own section. Only when a multi-system or cross-PR flow is genuinely hard
to narrate in prose, drop a small fenced-code-block diagram (arrows) inline into
whichever section it belongs to (see the example's "Overall approach"). Most briefs
don't need one at all. Don't pad the document to look thorough — reviewers are
overwhelmed by length, not impressed by it.

`reference/example-brief-initiative.md` is the other shape: use it instead when the
story describes a body of work or a process change rather than one feature or fix
(Goal, TLDR, process, setup tasks, impact levels, challenges).

Both share the same non-negotiables: every claim grounded in the actual current code
or story (not invented), the *why* and the *alternative you set aside* stated as a
decision (not posed as a question), and an explicit, three-axis read on anticipated
impact.

## What makes a brief good (the whole point)

1. **Grounded in the real, current code — not assumptions.** A brief that only
   restates the story is worthless — the reviewer can read the story. Open the
   codebase as it stands today, find where this would land, and cite it when it
   matters: `web_search.py:64-74 already turns a failed search into a default string
   — the retry logic would sit right after that`. There is no diff yet; you're
   grounding a plan, not describing a change.
2. **States decisions, not questions.** For each non-obvious call, say what you'd do
   and name the alternative you considered and set aside, with the reason — see the
   example's "Key design, and why not X". Do this even when you're not fully certain;
   a stated opinion with reasoning is more useful to a reviewer than an open-ended
   question, and it's what actually gets a fast "yes, agreed" or "no, because Y".
3. **Only raises a question when it's genuinely unresolved — and asks the author
   first.** If something really is a fork only the story's author can resolve, don't
   put a generic question in the brief as a first move. Ask the person you're
   building the brief with, directly, in this conversation. Only add an "Open
   questions" section, with that specific question, if they don't have an answer or
   tell you to leave it open for reviewers. Never pad this section with reflexive
   questions like "does this approach make sense?" or "any concerns?" — if there's
   nothing genuinely open, omit the section.
4. **States the anticipated impact on three axes**, every time: production,
   development, and — whenever the change touches env vars, secrets, feature flags,
   config, or a DB/infra migration — deployment. See below.
5. **Adapts to the unit of work.** A single feature/fix gets one narrative. Split
   into a PR breakdown table when the actual scope — grounded in the codebase, not
   in whether the tracker labels it an epic — doesn't fit into one atomic, reviewable
   PR; a story tagged as an epic can still turn out to be one small PR once you trace
   the code, and an untagged story can turn out to need a split. Add a merge-order /
   dependency note when one PR stacks on another unmerged branch (see the example's
   "Stacked on ACC-213" line). A broader initiative gets goal/process/impact framing
   instead.
6. **Plain language, English, short.** No machine-report tone, no em dashes, no
   jargon the story didn't already use. Write it the way you'd explain the plan to a
   teammate at a whiteboard — a handful of clear points, not an essay.

## Workflow

### 1. Resolve the target — wherever the story actually lives

This skill does not assume Jira. Teams track work differently — Jira, a GitHub
Issues/Projects board, Linear, Asana, ClickUp, Notion, or sometimes nothing more
than a paragraph of plain text or a Slack thread. Resolve from whatever is actually
in use, in this order:

- If `$ARGUMENTS` looks like a ticket ID or URL and a matching MCP is connected in
  this session (Atlassian for Jira, or Linear / Asana / Notion / GitHub for their
  respective trackers), fetch it there.
- If no matching MCP is connected, or the fetch fails, don't fail the whole task:
  say so plainly and ask the user to paste the story's title, description, and
  acceptance criteria directly, or point you at the right doc/issue/board card.
- If `$ARGUMENTS` is empty, ask the user to point you at the story or just describe
  it to you.

Whatever the source, you need the same three things before moving on: the title, the
problem/acceptance criteria, and any linked or sibling stories (this is how you find
out it's one PR among several planned ones). Tell the user what you resolved and
proceed.

### 2. Read the story

Pull: summary, problem/acceptance criteria, type, and linked/sibling items — a parent
epic or sibling stories are a signal the work might span multiple PRs, but the actual
call still comes from reading the code in step 3, not from this label. If there's a
parent epic, its description often holds the real problem statement worth pulling in.
If a tool call fails or nothing is connected, ask the user to paste the text instead
of stalling on it.

### 3. Read the current codebase — context first, not a diff

There is no diff to read — the point is to understand the codebase *as it stands
today* well enough to ground a specific, concrete plan. Work from the current default
branch (`master`/`main`), or from a dependency branch the story explicitly stacks on.
**Never mutate the working tree to get there** — the user may have uncommitted work
on their current branch, and checking out another branch's files over it would
silently discard it:

```bash
git fetch origin
git status --porcelain   # if this prints anything, the tree is dirty — don't touch it
```

- If already on `master`/`main` and clean, just read the files in place.
- Otherwise, read the target branch's files without touching the working tree —
  `git show origin/master:path/to/file`, or `git worktree add /tmp/pr-brief-ref origin/master`
  for a throwaway read-only checkout — instead of `git checkout <branch> -- .`.

Then, for the area the story touches:
- **Find where this would land.** Open the relevant files in full (not just grep
  hits) and trace the existing pattern — who calls what, what shape the data already
  has, what the nearest analogous feature looks like today.
- **Check the story's assumptions against the code.** If the story assumes something
  that isn't true today (the way the example brief found the existing delete flow
  already built and only reversibility missing), say so — that reframes the whole
  scope.
- **Judge whether this is one PR or several — from the code, not the tracker.**
  Would one PR, given the module boundaries and blast radius you're actually seeing,
  still be atomic and reviewable in one sitting? If not, split along those existing
  boundaries so each resulting PR is atomic on its own (mergeable independently,
  leaves the default branch in a working state), and note if one PR depends on a
  branch that isn't merged yet. Do this even if the tracker never called it an epic
  — and don't split just because it's labeled one, if the actual change is small.

Capture the `file:line` anchors that actually matter as you go — you'll cite them
where they ground a claim, not everywhere.

### 4. Write the brief (markdown, default output)

Write `pr_brief_<TICKET>.md` (or `pr_brief_<short-name>.md` when there's no ticket
ID) to the repo root. Follow `reference/example-brief.md`'s shape and length — 4-6
titled sections, omit whatever doesn't apply:

- **Title + TLDR**: `TICKET — <one line: what you intend to do and why>`, then 1-2
  sentences that let a reviewer who stops there still know the plan and its size.
  A one-line **dependency/stacking note** goes right after if relevant.
- **Problem**: what the story says versus what's actually true in the code today.
  Ground it, but keep it to a few sentences.
- **Overall approach**: the proposed shape, short and direct, present/future tense
  ("would add", "the plan is to"). If a multi-system or cross-PR flow is genuinely
  hard to narrate in prose, drop a small fenced-code-block diagram (arrows) in here
  — this is rare, not a section of its own, and most briefs skip it entirely.
- **PR breakdown** (only when the change doesn't fit one atomic, reviewable PR —
  a property of the code's actual size and blast radius, not of whether the tracker
  calls it an epic): a table — PR, story, what it builds, files it would touch, why
  this order — plus one line on atomicity: does each PR stand alone (mergeable by
  itself, default branch stays consistent if it's the only one that lands)?
- **Key design, and why not X**: one section, several bolded points inside it (not
  separate headers), each a decision you'd make plus the alternative you're setting
  aside and why. This is the section reviewers actually respond to.
- **Anticipated impact**: three axes, one short paragraph each, only the ones that
  apply:
  - **Production impact** (None/Low/Medium/High + why, tied to which code paths).
  - **Development impact** (None/Low/Medium/High + why, tied to scope of work).
  - **Deployment impact** — mandatory whenever the change touches env vars, secrets,
    feature flags, config defaults, or a DB/infra migration. State what has to happen
    operationally when this ships (a var to set, a migration to run before deploy, a
    flag's default). Omit only when genuinely nothing operational changes.
- **Open questions for reviewers**: only if something is genuinely unresolved after
  you asked the author directly (see point 3 above). Short — one or two real
  questions, never filler. Omit the section entirely if there's nothing open.

Rules: short over comprehensive; a handful of titled sections, prose within them, not
a header per sub-point; `file:line` where it grounds a claim, not as a checkbox;
present/future tense, a proposal, not a report; English; no em dashes; no invented
facts — if you didn't verify it, say "per the story" or omit it.

### 5. Render a visual only when it adds real value

The markdown file is the deliverable and is always produced. Generate HTML (or
another visual) only when it actually helps — a long brief that benefits from a
light/dark reading page, or a flow/split that's genuinely clearer as an image than
the fenced-code-block diagram already covers. For a normal brief, the markdown alone
is enough — most briefs should stop here.

When it's warranted:

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
open pr_brief_<TICKET>.html      # macOS; xdg-open on Linux; start on Windows
```

If `open`/`xdg-open`/`start` is unavailable, just report the path instead.

Show the user the markdown path (and HTML path if generated) with a short summary of
what you're proposing.

## Not this

- Not a code review. No severities, no findings — there's no code to review yet.
- Not a description of a diff or a finished change. If it reads like a report of
  something already built, it's the wrong tense.
- Not a story restatement. If it could've been written without opening the current
  codebase, it failed.
- Not a wall of generic questions. State a decision and its reasoning by default;
  only ask when it's genuinely unresolved, and only after asking the author first.
- Not an essay. If it needs more than 4-6 titled sections to say, cut it down before
  you send it.
