# claude-pr-brief-md

Pre-implementation design brief skill for [Claude Code](https://claude.ai/code).
Clone this repo, open Claude Code, and it walks you through installing it — into
every project, or just one, shared with your team via git.

A brief is what you send reviewers right after a story exists — the problem, your
proposed approach, a handful of key design calls (each a stated decision with the
alternative you set aside, not a question left dangling), and the anticipated impact
across production, development, and deployment. It's sent *before* you write the
code, so reviewers can weigh in while changing the plan is still cheap. Tracker-agnostic
by design — Jira, GitHub Issues/Projects, Linear, Asana, Notion, or just pasted text
all work, so the whole team can share one skill regardless of how they track work.

## Quick Start

```bash
git clone https://github.com/RBalan37/claude-pr-brief-md.git
cd claude-pr-brief-md
# Open Claude Code here — it will ask a couple of quick questions and install itself
```

Claude will ask you:

1. Install globally (every project) or into one specific project's `.claude/`?
2. What to name the skill (default `pr-brief`, i.e. the `/pr-brief` command)
3. If project-scoped, which project

Then it installs the skill directly into the right place.

## Manual Install (without Claude driving it)

```bash
cd /path/to/claude-pr-brief-md
chmod +x install.sh
./install.sh
```

Answer its two or three prompts the same way. Global install goes to
`~/.claude/skills/<name>`; project install goes to `<project>/.claude/skills/<name>`
— commit that folder if you want the rest of the team to get it when they pull.

## What Gets Installed

```
<destination>/.claude/skills/<name>/
  SKILL.md                              # the skill itself (becomes the /<name> command)
  generate_brief_html.py                # markdown → self-contained HTML renderer
  reference/
    example-brief.md                    # worked example (fictional scenario)
    example-brief-initiative.md         # broader initiative/project example
```

## Usage (after install)

Right after a story exists — in Jira, a GitHub issue, Linear, or just described in
chat — invoke the skill before writing any code:

```
/pr-brief ACC-214
/pr-brief https://github.com/org/repo/issues/42
/pr-brief
```

(Use whatever name you chose at install time instead of `pr-brief` if you renamed it.)

Without an argument, the skill asks you to describe the story directly. If no
tracker MCP is connected (Jira/Linear/Asana/Notion/GitHub), it asks you to paste the
story text instead of failing — no specific tracker is required.

The skill always writes `pr_brief_<TICKET>.md` to the repo root. It only renders
HTML on top of that when a visual genuinely helps (a long brief, or a flow clearer
as an image):

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md \
  --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
```

Send the markdown (or HTML) to reviewers before you start coding.

### Ticket quality matters

The brief is only as good as the ticket plus the code — Claude can't invent a goal,
a problem statement, or acceptance criteria that were never written down, and it
won't guess at them and pass the guess off as fact. If a ticket is just a title with
no description, expect Claude to ask you specific questions to fill exactly what's
missing (the problem it solves, what done looks like, who's affected) before it
writes anything — not to flag the gap and move on, and not to produce a brief built
on an assumption nobody confirmed. For a brief you can actually hand to reviewers
with no back-and-forth, write tickets with at least:

- a **title** (what),
- a **goal or problem statement** (why), and
- **acceptance criteria** (what "done" looks like).

## Prerequisites

- [Claude Code](https://claude.ai/code) installed
- `python3` (for the HTML renderer, only needed when you use it)
- Optional, and auto-detected at run time — not required: a tracker MCP connected
  (Atlassian for Jira, or Linear / Asana / Notion / GitHub)

## Brief Structure

4-6 titled sections total, prose within each — not a header per sub-point. See
`templates/reference/` for full worked examples.

**Single feature/fix, or work split across multiple atomic PRs**
(`templates/reference/example-brief.md`, a worked example):

| Section | What it covers |
|---|---|
| **Title + TLDR** | One line on what you intend to do and why, then 1-2 sentences for the whole plan. A one-line dependency/stacking note if the work stacks on another unmerged branch. |
| **Problem** | What the story says versus what's actually true in the code today. A few sentences, grounded where it matters. |
| **Overall approach** | The proposed shape, short and direct, present/future tense. Rarely, a multi-system flow that's genuinely hard to narrate in prose gets a small inline diagram (fenced code block, arrows) here — not its own section. |
| **PR breakdown** | *(Only when the change doesn't fit one atomic, reviewable PR — judged from the codebase, not from whether the tracker calls it an epic)* Table: PR, story, what it builds, files, why this order — plus a note that each PR stands alone (mergeable by itself, default branch stays consistent). |
| **Key design, and why not X** | One section, several bolded points inside it. Each states a decision and the alternative set aside — not a question. This is the section reviewers actually respond to. |
| **Anticipated impact** | *(Mandatory)* Production impact, Development impact, and Deployment impact whenever env vars/config/flags/migrations are touched. |
| **Open questions for reviewers** | *(Only if genuinely unresolved after asking the author directly.)* Short, never filler. Omit if there's nothing open. |

**Broader initiative / project** (`templates/reference/example-brief-initiative.md`):
Goal, TLDR, the process/flow itself, setup tasks, deliverables, the same mandatory
impact axes, and Challenges/risks.

### Quality bar

- **Grounded in the current code**, not the story text alone. `file:line` where it
  genuinely grounds a claim — not as a formality on every sentence.
- **States decisions, not questions.** Name the alternative you set aside and why,
  even when you're not fully certain. A stated opinion beats an open-ended question.
- **Open questions are rare and specific.** Ask the story's author directly first;
  only put a question in the brief if they don't have an answer or say to leave it.
- **Three-axis impact, every time**: production, development, and deployment when
  relevant (migrations, env vars, feature flags, config).
- **Short.** 4-6 titled sections, prose inside them, no essay. Reviewers are
  overwhelmed by length, not impressed by it.
- **Tracker-agnostic.** Works from Jira, GitHub, Linear, Asana, Notion, or plain text.
- **Written before the code exists.** Present/future tense, a proposal, not a report.
- **English.** No em dashes. No invented facts.

## Customization

After installation, edit the installed `SKILL.md` directly to adjust section order,
loosen or tighten the length target, or change what counts as a mandatory impact
axis. `templates/` in this repo is the source of truth if you want to change the
defaults for future installs (including teammates').

## License

MIT — see [LICENSE](LICENSE).
