# claude-pr-brief-md

Claude Code skill for writing **reviewer-facing PR briefs**: plain-language context grounded in `file:line` citations, with markdown output and a self-contained HTML reading view.

A brief is what a reviewer reads *before* the diff — it explains the problem, the fix, key design decisions (and rejected alternatives), and the blast radius. It is **not** a code review.

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

In Claude Code, invoke the skill when you want a brief for a PR, branch, or Jira ticket:

```
/brief AMVP-156149
/brief 4821
/brief
```

The skill writes `pr_brief_<TICKET>.md` and renders HTML with:

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md \
  --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
```

## Brief structure

Every brief should follow this shape (omit sections that do not apply):

| Section | What it covers |
|---|---|
| **Title** | `TICKET — one line: what it does and why` |
| **Problem** | 2–4 sentences on the current state and why it is inadequate. Cite the limiting code (`file.py:line`). |
| **Fix** | High-level solution shape in plain prose. |
| **Design sections** | One titled block per non-obvious decision. Every claim carries a `file:line`. Include a **Key design** section that names the rejected alternative and explains why it was rejected. |
| **Open decisions** | Anything undecided, who owns it, and what changes once decided. |
| **Data / control flow** | End-to-end walkthrough when the change adds or reroutes a path. |
| **Blast radius** | What this touches, which behaviours change, scale/fan-out, and where risk concentrates. Quantify when you can. |
| **PR breakdown** | *(Epics only)* One subsection per PR — ticket, files, and what each changes. |

### Quality bar

- **Grounded in code**, not the PR description. Open the branch and cite exact sites.
- **Explains why**, not just what. Name the obvious alternative and say why it was rejected.
- **Names open decisions** — do not pretend everything is settled.
- **Prose over bullet dumps.** Write the way you would explain it at a whiteboard.
- **English.** No em dashes. No invented facts.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Skill instructions for Claude Code |
| `generate_brief_html.py` | Markdown → self-contained HTML renderer (light/dark toggle, section nav) |
