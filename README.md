# claude-pr-brief-md

Claude Code skill for writing **reviewer-facing briefs**: short, direct, plain-language
context grounded in the actual code (`file:line` citations), with markdown output and,
when it's genuinely useful, a self-contained HTML reading view.

A brief is what a reviewer reads *before* the diff — it explains the problem, the fix,
key design decisions (and rejected alternatives), whether the change touches
production, and the blast radius. It is **not** a code review.

## Install

```bash
git clone https://github.com/RBalan37/claude-pr-brief-md.git
mkdir -p ~/.claude/skills/pr-brief
cp -r claude-pr-brief-md/* ~/.claude/skills/pr-brief/
```

Or symlink so you edit in one place:

```bash
ln -s "$(pwd)/claude-pr-brief-md" ~/.claude/skills/pr-brief
```

## Usage

In Claude Code, invoke the skill when you want a brief for a PR, branch, Jira ticket,
or a broader initiative:

```
/brief AMVP-156149
/brief 4821
/brief
```

The skill always writes `pr_brief_<TICKET>.md`. When a visual genuinely helps (a
longer brief, an epic with several PRs, a flow that's clearer as a picture), it also
renders HTML:

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md \
  --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
```

## Brief structure

There are two shapes, depending on the unit of work — see `reference/` for full
worked examples of both.

**Single PR / bug fix / epic-of-PRs** (`reference/example-brief.md`):

| Section | What it covers |
|---|---|
| **Title** | `TICKET — one line: what it does and why` |
| **TLDR** | 1–2 sentences, the whole thing in miniature |
| **Problem** | 2–4 sentences on the current state and why it is inadequate. Cite the limiting code (`file.py:line`). |
| **Fix** | High-level solution shape, short and direct. |
| **Design sections** | One titled block per non-obvious decision. Every claim carries a `file:line`. Include a **Key design** section that names the rejected alternative and explains why it was rejected. |
| **Open decisions** | Anything undecided, who owns it, and what changes once decided. |
| **Data / control flow** | End-to-end walkthrough when the change adds or reroutes a path. |
| **Impacts** | *(Mandatory)* Production impact level and Development impact level, each with the reasoning tied to which code paths are touched. |
| **Blast radius** | What this touches, which behaviours change, scale/fan-out, and where risk concentrates. |
| **PR breakdown** | *(Epics only)* One subsection per PR — ticket, files, and what each changes. |

**Broader initiative / project** (`reference/example-brief-initiative.md`): Goal,
TLDR, the process/flow itself, setup tasks, deliverables, the same mandatory
**Impacts** section, and Challenges/risks.

### Quality bar

- **Grounded in code**, not the PR description. Open the branch and cite exact sites.
- **Explains why**, not just what. Name the obvious alternative and say why it was rejected.
- **Names open decisions** — do not pretend everything is settled.
- **States whether it touches production**, explicitly, every time.
- **Short and direct over comprehensive.** Bullets for concrete lists, prose only for the *why*.
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
