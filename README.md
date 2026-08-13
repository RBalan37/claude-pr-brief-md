# claude-pr-brief-md

Claude Code skill for writing **pre-implementation design briefs**: short, direct,
plain-language proposals grounded in the current codebase (`file:line` citations),
sent to reviewers *before* you write the code, so they can weigh in on the plan while
it's still cheap to change.

A brief is what you send right after creating the Jira story — it lays out the
problem, your intended approach, the key design decisions (and alternatives you
considered and set aside), the open questions you want the reviewer's take on, and
the anticipated impact. It is **not** a code review, and it is not a description of a
diff — there isn't one yet.

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
unchanged — `~/.claude/skills/pr-brief` resolves the same way. Native PowerShell
equivalent, if you're not using either:

```powershell
git clone https://github.com/RBalan37/claude-pr-brief-md.git
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills\pr-brief"
Copy-Item -Recurse -Force claude-pr-brief-md\* "$env:USERPROFILE\.claude\skills\pr-brief\"
```

One OS-specific detail inside the skill itself: step 5 opens the rendered HTML with
`open` (macOS) or `xdg-open` (Linux). On Windows, use `start` instead, or just open
the `.html` file from Explorer.

## Usage

Right after creating a Jira story, invoke the skill to structure your intended
approach before writing any code:

```
/brief AMVP-156149
/brief
```

Without a key, the skill asks you to describe the story directly (title, problem,
rough approach) and briefs from that.

The skill always writes `pr_brief_<TICKET>.md`. When a visual genuinely helps (a
longer brief, an epic planned across several PRs, a flow that's clearer as a
picture), it also renders HTML:

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md \
  --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
```

Send the markdown (or HTML) to reviewers before you start coding — the point is to
get their reaction to the plan while changing it is still free.

## Brief structure

There are two shapes, depending on the unit of work — see `reference/` for full
worked examples of both.

**Single feature/fix, or an epic planned across PRs** (`reference/example-brief.md`):

| Section | What it covers |
|---|---|
| **Title** | `TICKET — one line: what you intend to do and why` |
| **TLDR** | 1–2 sentences, the whole plan in miniature |
| **Problem** | 2–4 sentences on the current state and why it is inadequate. Cite the limiting code (`file.py:line`). |
| **Proposed approach** | High-level solution shape, written as a proposal, short and direct. |
| **Design sections** | One titled block per non-obvious decision you're planning. Every claim carries a `file:line` into the current codebase. Include a **Key design, and why not X** section that names the alternative you considered and why you'd set it aside. |
| **Open questions for reviewers** | The things you're genuinely unsure about, posed as direct questions — the whole point of sending this before you code. |
| **Data / control flow** | End-to-end walkthrough of the path the change would add or reroute. |
| **Anticipated impact** | *(Mandatory)* Anticipated Production impact level and Development impact level, each with the reasoning tied to which code paths would be touched. |
| **PR breakdown** | *(Epics only)* One subsection per planned PR — rough scope, files, what it would change. |

**Broader initiative / project** (`reference/example-brief-initiative.md`): Goal,
TLDR, the process/flow itself, setup tasks, deliverables, the same mandatory
**Impacts** section, and Challenges/risks.

### Quality bar

- **Grounded in the current code**, not the ticket text. Open the codebase as it
  stands today and cite exact sites for where the plan would land.
- **Explains why this shape, not just what.** Name the obvious alternative and say
  why you'd set it aside — written to invite disagreement, not just to inform.
- **Poses open questions to the reviewer**, directly, with your own leaning if you
  have one — do not pretend everything is already decided.
- **States anticipated production impact**, explicitly, every time.
- **Written before the code exists.** Present/future tense, a proposal, not a report
  of something already built.
- **Short and direct over comprehensive.** Bullets for concrete lists, prose only for
  the *why*.
- **English.** No em dashes. No invented facts.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Skill instructions for Claude Code |
| `generate_brief_html.py` | Markdown → self-contained HTML renderer (light/dark toggle, section nav) |
| `reference/example-brief.md` | Worked example: single PR, grounded in `file:line` citations |
| `reference/example-brief-initiative.md` | Worked example: broader initiative/project brief |

## License

MIT — see [LICENSE](LICENSE).
