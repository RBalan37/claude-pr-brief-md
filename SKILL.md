---
name: pr-brief
description: Produce a short, direct design brief for a Jira story/ticket, written BEFORE the code change exists — a plain-language document that lays out the problem, the intended approach, the key design decisions (with alternatives considered), and the anticipated impact, so a reviewer can weigh in on the plan and say "why this and not that" before any code is written. Grounded in the current codebase (file:line) — where the change would land and what patterns already exist there — not in a diff, because there isn't one yet. Adapts to a single fix/feature, an epic planned across several PRs, or a broader initiative. Writes a markdown file (pasteable into the Jira story or sent to reviewers directly) and, when a visual would genuinely help, renders one too. Use right after creating the Jira story, when asked to "brief", "write up", "plan out", or "structure my thoughts on" a feature or fix before implementation starts. NOT a code review and NOT a description of a finished change — it proposes, it does not report; use pr-review-html for post-hoc findings.
allowed-tools: Bash, Read, Write, Grep, Glob, WebFetch, mcp__atlassian__getJiraIssue, mcp__atlassian__searchJiraIssuesUsingJql
argument-hint: "[Jira key | nothing = describe the story to me]"
---

# PR Brief → pre-implementation design brief for reviewers

Generate a **brief**: the document you send reviewers *before you write the code*,
right after the Jira story exists, so they can react to the plan — agree with it,
push back on it, or suggest a different shape — while it's still cheap to change.
It is not a report of what you built; there is nothing built yet. It is a proposal,
grounded in the real codebase as it stands today, that structures your own thinking
enough to hand it to someone else and ask "does this make sense, or should it be
different?"

Keep it short, direct, and easy to skim. The goal is to get your intended approach
across cleanly enough that a reviewer can form an opinion in a few minutes — not to
demonstrate thoroughness. Use bullets for lists of concrete things (setup steps,
files that would be touched, open questions) and short prose only where an
explanation genuinely needs a sentence or two, e.g. the *why* behind a choice.
Favor a "TLDR" or "Goal" line up top over a long lead-in.

Two gold-standard examples live in `reference/`:
- `example-brief.md` — a single feature/fix or an epic planned across several PRs,
  grounded in `file.py:line` citations into the *current* codebase. Written before
  any of it exists, as a proposal open to pushback.
- `example-brief-initiative.md` — a broader initiative / project brief (goal, TLDR,
  process, setup tasks, impact levels, challenges). Use this shape when the ticket
  describes a body of work or a process change rather than one feature or fix.

Read whichever is the closer match before you start. Both share the same non-negotiables:
every claim grounded in the actual current code or ticket (not invented), the *why*
and the *alternative you considered and set aside* made explicit for non-obvious
decisions, open questions named as open and posed *to the reviewer*, and an explicit
read on the anticipated impact.

## What makes a brief good (the whole point)

1. **Grounded in the real, current code — not assumptions.** A brief that only
   restates the ticket is worthless — the reviewer can read the ticket. The value is
   that you *opened the codebase as it stands today*, found where this would land,
   and cite the exact site: `web_search.py:64-74 already turns a failed search into
   a default string — the new retry logic would sit right after that`. There is no
   diff to read yet; you are grounding a plan, not describing a change.
2. **Explains why this shape, not just what you'd build.** Say what you intend to do,
   then, crucially, **name the obvious alternative and why you'd set it aside**. The
   example's "Key design, and why not X" section is the template. This is the part
   reviewers actually respond to — it's an invitation to disagree, not a summary.
3. **Poses the open questions to the reviewer.** This is the point of sending the
   brief before coding: surface exactly what you're unsure about ("should tenancy be
   global or per-class? I'd lean X, wanted your take before I build around it") and
   ask directly. A brief that pretends everything is decided defeats its own purpose.
4. **States the anticipated impact.** What would this touch once built? Which
   existing behaviours would change? Where would risk concentrate? You're estimating,
   not reporting — say so where you're not certain.
5. **Adapts to the unit of work.** A single feature/fix gets one narrative. An epic
   planned across PRs (PR 1 the table, PR 2 the job, ...) gets a per-PR breakdown of
   the *plan* — see `example-brief.md`. A broader initiative gets goal/process/impact
   framing instead — see `example-brief-initiative.md`.
6. **Says plainly what production impact to expect.** Not optional. Read the proposed
   change against the existing codebase and state, explicitly, an anticipated
   production impact level and development impact level (see
   `example-brief-initiative.md`'s "Impacts" section for the format), with the
   reasoning tied to which code paths would actually be touched.
7. **Plain language, English, and genuinely inviting feedback.** No machine-report
   tone, no em dashes, no jargon the ticket didn't already use. Write it the way
   you'd explain the plan to a teammate at a whiteboard and then ask "what do you
   think?" — because that's literally what the last section should do.

## Workflow

### 1. Resolve the target — the Jira story you just created

`$ARGUMENTS` is a Jira key (`AMVP-156149`), or empty.

- **Given a Jira key**: fetch the ticket (step 2). Also check for a linked parent
  epic or sibling stories — that's how you discover this is one PR among several
  planned ones. If a branch already exists for it (`git branch --list "*<KEY>*" -a`)
  note it, but its existence doesn't change anything here: you're briefing the plan,
  not the branch's contents.
- **Given nothing**: ask the user for the Jira key, or ask them to describe the story
  directly (title + problem + rough approach) so you can proceed without one.

Tell the user what you resolved (ticket, and epic/siblings if any) and proceed.

### 2. Read the Jira ticket

Use `mcp__atlassian__getJiraIssue` with the key (set the cloud ID for your org).
Pull: summary, description (acceptance criteria / problem statement), issue type,
labels/components, and **linked issues** — a parent epic or sibling tickets are how
you discover an epic-planned-across-PRs. Fetch the parent epic too when there is one;
it often holds the real problem statement. If the ticket is inaccessible, ask the
user to paste the ticket text instead.

If the atlassian MCP is not connected in this session, don't fail: ask the user to
paste the ticket text, or work from what they tell you directly, and note that the
Jira context is from what was provided, not the tracker itself.

### 3. Read the current codebase — context first, not a diff

This is the step that separates a real plan from a paraphrase of the ticket. There is
no diff to read — the point is to understand the codebase *as it stands today* well
enough to propose a specific, groundable design. Work from the current default branch
(`master`/`main`), not a feature branch with in-progress changes:

```bash
git fetch origin
git checkout origin/master -- .   # or just read in place if already on master/main
```

Then, for the area the story touches:
- **Find where this would land.** Open the relevant files in full (not just grep hits)
  and trace the existing pattern: who calls what, what shape the data already has,
  what the nearest analogous feature looks like today. Cite it (`playbook_dao.py:24`)
  — this is what makes the proposal concrete instead of hand-wavy.
- **Check the ticket's assumptions against the code.** If the story assumes something
  that isn't true today, say so — that's exactly the kind of thing a reviewer needs
  to see before you start building on a wrong assumption.
- **For an epic**, sketch how the work would split across PRs and what each would
  touch, based on the existing module boundaries.

Capture the concrete `file:line` anchors as you go — you will cite them in the brief
as the grounding for your *proposed* design, not as a description of changes made.

### 4. Write the brief (markdown, default output)

Write `pr_brief_<TICKET>.md` (or `pr_brief_<short-name>.md` when there is no ticket
key yet) to the repo root — pasteable into the Jira story or sent to reviewers
directly, renders on GitHub.

**For a single feature/fix, or an epic planned across PRs**, follow `example-brief.md`'s
shape — omit any section that does not apply:

- **Title**: `TICKET — <one line: what you intend to do and why>`.
- **TLDR**: 1-2 sentences, the whole plan in miniature. A reviewer who stops here
  should still know what you're proposing and roughly how big a deal it is.
- **Problem**: 2-4 sentences. The state of the world today and why it's inadequate.
  Ground it: cite the current code that has the limitation.
- **Proposed approach**: the high-level shape of the intended solution, short and
  direct. Written as a proposal ("I'd add...", "the plan is to..."), not as a report.
- **Design sections** (only as many as the change actually warrants) covering the
  non-obvious decisions you're planning to make and, for each, the *why*. Include a
  **"Key design, and why not X"** section that names the alternative you considered
  and why you'd set it aside, whenever your plan deliberately departs from an
  existing pattern in the codebase.
- **Open questions for reviewers**: the things you're genuinely unsure about, posed
  as direct questions, with your own leaning stated if you have one. This is the
  section the whole brief exists to set up — don't skip it or make it token.
- **Data / control flow**: a short walkthrough of the end-to-end path the change
  would add or reroute ("the user would select devices ... the researcher would hand
  them to the writer"). A small diagram is fine here instead of prose if it's clearer.
- **Anticipated impact**: state an **anticipated Production impact level** and
  **Development impact level** (None / Low / Medium / High), each with one sentence
  of reasoning tied to which code paths would be touched. Mandatory, not optional.
  Say plainly where you're estimating versus certain.
- **PR breakdown** (only for an epic): one subsection per planned PR — its rough
  scope, the files it would likely touch, and what it changes. See the example's
  `PR 1 … PR 4`, framed as the plan rather than a report.

**For a broader initiative / project** (a ticket describing a process or a body of
work rather than one feature or fix), follow `example-brief-initiative.md`'s shape
instead: Goal, TLDR, the process/flow itself, setup tasks, the concrete deliverables
(bulleted), an **Impacts** section (same anticipated Production/Development impact
levels as above), and Challenges/risks. Bullets are expected here, not a flaw.

Rules either way: short and direct over comprehensive; bullets for lists of concrete
things, prose only for the *why*; every design claim carries a `file:line` when
current code exists to point at; written as a proposal, present/future tense, not
past tense describing something already built; English; no em dashes; no invented
facts — if you didn't verify it against the current code, don't assert it (say "per
the ticket" or omit). Match the relevant example's register.

### 5. Render a visual when it adds value

The markdown file is the deliverable and is always produced. An HTML reading view
(or another visual, e.g. a diagram/schema image) is worth generating **when it
actually helps** — a longer brief, an epic with several planned PRs, or a data/control
flow that's genuinely clearer as a picture than a paragraph. For a short, simple
brief, the markdown file alone is enough — don't generate HTML just because you can.

When it's warranted:

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
open pr_brief_<TICKET>.html      # macOS; use xdg-open on Linux
```

The generator renders the markdown into a clean reading page with a light/dark toggle
and a sticky section nav. If `open` is unavailable (headless / Linux without a
browser), just report the path instead.

Then show the user the markdown path (and the HTML path if you generated one) with a
short summary of what you're proposing and what you're asking reviewers to weigh in on.

## Not this

- Not a code review. No severities, no findings, no "you should fix" — there's no
  code to review yet. For findings on an actual change, use `pr-review-html`.
- Not a description of a diff or a finished change. If the brief reads like a report
  of something already built, it's the wrong tense — this is written before the work.
- Not a ticket restatement. If it could have been written without opening the current
  codebase, it failed — the plan needs to be grounded in what's actually there today.
- Not a document that pretends everything is settled. If the "Open questions for
  reviewers" section is empty or token, either the plan genuinely has no open
  questions (rare) or you haven't looked hard enough for them.
