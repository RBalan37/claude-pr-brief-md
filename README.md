# claude-pr-brief-md

Claude Code skill for writing reviewer-facing PR briefs: plain-language context grounded in `file:line` citations, with markdown output and a self-contained HTML reading view.

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

The skill writes `pr_brief_<TICKET>.md` and renders it with:

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md \
  --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
```

See `reference/example-brief.md` for the target structure and tone.

## Files

- `SKILL.md` — skill instructions for Claude Code
- `generate_brief_html.py` — markdown to self-contained HTML renderer
- `reference/example-brief.md` — gold-standard example brief
