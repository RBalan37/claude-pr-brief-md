# Installing the pr-brief skill

You are running inside a freshly cloned copy of this repo. The person just wants the
`pr-brief` skill installed — walk them through a couple of quick questions, then
install it. Don't dump all the questions at once; ask one, wait, ask the next.

## Ask, in order

1. **Scope** — "Install globally, so it's available in every project, or into one
   specific project's `.claude/` folder (so it gets committed and shared with that
   project's team via git)?" Default if they have no preference: global.
2. **Skill/command name** — "What should the slash command be called? Default is
   `pr-brief` (so `/pr-brief`)." Most people should just keep the default — only
   rename if they already have a conflicting skill or a house convention.
3. **If they chose project scope**: "Which project — give me the path." Default to
   the current directory if they don't have one in mind.

## Then install

Run the installer rather than reimplementing its logic by hand:

```bash
chmod +x install.sh
./install.sh
```

Answer its prompts with what the person told you above (pipe them in, or just let
the person answer the prompts directly — either works).

## Verify

List the destination directory afterward and confirm `SKILL.md`,
`generate_brief_html.py`, and `reference/example-brief.md` +
`reference/example-brief-initiative.md` are all present. Tell the person the exact
command going forward: `/<skill-name> <ticket-id-or-URL>` (or just `/<skill-name>`
with nothing, which prompts them to describe the story instead).

If they chose project scope, remind them to commit the new `.claude/skills/...`
files so the rest of the team gets the skill too.

## Don't

- Don't guess the scope or the name — ask.
- Don't hand-copy files instead of running `install.sh` — the script also keeps the
  `SKILL.md` frontmatter's `name:` field in sync with a renamed command, which a
  manual copy would miss.
- Don't install into both scopes without being asked to.
