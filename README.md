# claude-pr-brief-md

Claude Code skill for writing **pre-implementation design briefs**: short, direct
proposals grounded in the current codebase, sent to reviewers *before* you write the
code, so they can weigh in on the plan while it's still cheap to change. Tracker-agnostic
by design — works with Jira, GitHub Issues/Projects, Linear, Asana, Notion, or just
pasted text — so a whole team can share the same skill regardless of how they track work.

A brief is what you send right after a story exists — it lays out the problem, your
proposed approach, a handful of key design calls (each stated as a decision with the
alternative you set aside, not left as an open question), and the anticipated impact
across production, development, and deployment. It is **not** a code review, and it
is not a description of a diff — there isn't one yet.

## Install

**macOS / Linux:**

```bash
git clone https://github.com/RBalan37/claude-pr-brief-md.git
mkdir -p ~/.claude/skills/pr-brief
cp -r claude-pr-brief-md/* ~/.claude/skills/pr-brief/
```

Or symlink so you edit in one place:

```bash
ln -s "$(pwd)/claude-pr-brief-md" ~/.claude/skills/pr-brief
```

**Windows:** Claude Code runs under WSL or Git Bash, where the commands above work
unchanged. Native PowerShell equivalent, if you're not using either:

```powershell
git clone https://github.com/RBalan37/claude-pr-brief-md.git
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills\pr-brief"
Copy-Item -Recurse -Force claude-pr-brief-md\* "$env:USERPROFILE\.claude\skills\pr-brief\"
```

One OS-specific detail inside the skill itself: step 5 opens rendered HTML with
`open` (macOS), `xdg-open` (Linux), or `start` (Windows).

**Note:** never copy the `.git` folder into `~/.claude/skills/pr-brief` — use `*`
(not `.`) in the `cp` command above, or you'll hit permission errors on git's
internal (read-only) object files.

## Usage

Right after a story exists — in Jira, a GitHub issue, Linear, or just described in
chat — invoke the skill to structure your intended approach before writing any code:

```
/brief AMVP-156149
/brief https://github.com/org/repo/issues/42
/brief
```

Without an argument, the skill asks you to describe the story directly. If no
tracker MCP is connected (Jira/Linear/Asana/Notion/GitHub), it asks you to paste the
story text instead of failing — this skill never requires a specific tracker.

The skill always writes `pr_brief_<TICKET>.md`. It only renders HTML on top of that
when a visual genuinely helps (a long brief, or a flow clearer as an image):

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md \
  --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
```

Send the markdown (or HTML) to reviewers before you start coding.

## Brief structure

4-6 titled sections total, prose within each — not a header per sub-point. See
`reference/` for full worked examples.

**Single feature/fix, or an epic planned across PRs** (`reference/example-brief.md`,
a real brief that got good reviewer feedback):

| Section | What it covers |
|---|---|
| **Title + TLDR** | One line on what you intend to do and why, then 1-2 sentences for the whole plan. A one-line dependency/stacking note if the work stacks on another unmerged branch. |
| **Problem** | What the story says versus what's actually true in the code today. A few sentences, grounded where it matters. |
| **Overall approach** | The proposed shape, short and direct, present/future tense. |
| **PR breakdown** | *(Epics only)* Table: PR, story, what it builds, files, why this order — plus an atomicity note. |
| **Key design, and why not X** | One section, several bolded points inside it. Each states a decision and the alternative set aside — not a question. |
| **Data / control flow** | A small diagram (fenced code block, arrows) when a flow is involved. |
| **Anticipated impact** | *(Mandatory)* Production impact, Development impact, and Deployment impact whenever env vars/config/flags/migrations are touched. |
| **Open questions for reviewers** | *(Only if genuinely unresolved after asking the author directly.)* Short, never filler. Omit if there's nothing open. |

**Broader initiative / project** (`reference/example-brief-initiative.md`): Goal,
TLDR, the process/flow itself, setup tasks, deliverables, the same mandatory impact
axes, and Challenges/risks.

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

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Skill instructions for Claude Code |
| `generate_brief_html.py` | Markdown → self-contained HTML renderer (light/dark toggle, section nav) |
| `reference/example-brief.md` | Real, reviewer-approved example: single story split across 2 PRs |
| `reference/example-brief-initiative.md` | Worked example: broader initiative/project brief |

## License

MIT — see [LICENSE](LICENSE).
