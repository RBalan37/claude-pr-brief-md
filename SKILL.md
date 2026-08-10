---
name: pr-brief
description: Produce a reviewer-facing brief for a PR, branch, or Jira ticket — a plain-language document that explains the problem, the fix, the key design decisions (with their rejected alternatives), and the blast radius, so a reviewer understands the change before reading a single line of the diff. Every claim is grounded in the actual branch code (file:line), not just the diff or the PR description. Adapts to a single PR or an epic split across several PRs. Writes a markdown file (pasteable into the PR description or a Jira comment) and always renders it into a self-contained HTML that it opens in the browser. Use when asked to "brief", "write up", "explain", or "summarize" a PR/branch/ticket for reviewers. NOT a code review — it explains, it does not judge; use pr-review-html for findings.
allowed-tools: Bash, Read, Write, Grep, Glob, WebFetch, mcp__atlassian__getJiraIssue, mcp__atlassian__searchJiraIssuesUsingJql
argument-hint: "[Jira key | PR number/URL | nothing = current branch]"
---

# PR Brief → reviewer-facing context document

Generate a **brief**: the document a reviewer reads *first*, before the diff, so
they arrive at the code already knowing what problem it solves, what it does, why
it was built this way, and what could break. It is the opposite of a code review —
it does not hunt for findings or rate anything. It explains.

The gold-standard example lives in `reference/example-brief.md`. Read it before you
start. It sets the bar: prose, not bullets-for-their-own-sake; every design claim
grounded in a concrete `file.py:line`; the *why* and the *rejected alternative*
made explicit; open decisions named as open; and an epic-across-PRs mapped PR by PR.

## What makes a brief good (the whole point)

1. **Grounded in the real code, not the description.** A brief that only paraphrases
   the PR description is worthless — the reviewer can read the description. The value
   is that you *opened the branch*, traced the change, and cite the exact site:
   `web_search.py:64-74 turns a failed search into a default string and continues`.
   Verify the description's claims against the code; where they disagree, the code
   wins and you say so.
2. **Explains why, not just what.** The diff already shows *what* changed. The brief
   explains *why this shape* — and, crucially, **why not the obvious alternative**.
   The example's "Key design, and it is deliberately not the design of playbook"
   section is the template: name the alternative, say why it was rejected.
3. **Names the open decisions.** Real work has undecided parts ("tenancy is on
   stand by, Diogo to decide"). A brief that pretends everything is settled misleads
   the reviewer. Surface them.
4. **States the blast radius.** What does this touch that isn't obvious from the file
   list? Which existing behaviours change? What is the fan-out / scale? Where is the
   risk concentrated? This is what tells a reviewer where to spend their attention.
5. **Adapts to the unit of work.** A single self-contained PR gets one narrative. An
   epic split across PRs (PR 1 the table, PR 2 the job, ...) gets a per-PR breakdown
   with each PR's files and its own blast radius — see the example.
6. **Plain language, English.** Reviewers across the team read this. No machine-report
   tone, no em dashes, no jargon the ticket didn't already use. Write it the way you'd
   explain the change to a teammate at a whiteboard.

## Workflow

### 1. Resolve the target — ticket, PR, or branch

`$ARGUMENTS` is one of: a Jira key (`AMVP-156149`), a PR number/URL (`4821`), or empty.
Cross-link them so you end up with all three where they exist.

```bash
# empty → current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
# a branch name like rodrigo.balan.AMVP-157702-... carries the ticket key:
echo "$BRANCH" | grep -oE '[A-Z]+-[0-9]+'
```

- **Given a Jira key**: fetch the ticket (step 2). Find its PR(s):
  `gh pr list --search "AMVP-156149" --state all --json number,title,headRefName,url`
  (also try the branch-name convention). An epic may have several — note them all.
- **Given a PR number/URL**: `gh pr view $PR --json number,title,author,headRefName,baseRefName,body,additions,deletions,changedFiles,url`
  then extract the Jira key from the branch name or title and fetch the ticket.
- **Given nothing**: use the current branch; derive the key from its name; look for an
  open PR for it with `gh pr list --head "$BRANCH"`.

Tell the user what you resolved (ticket + PR(s) + branch) and proceed. If there is a
ticket key but no PR yet, that is fine — brief the branch against `master`.

### 2. Read the Jira ticket

Use `mcp__atlassian__getJiraIssue` with the key (set the cloud ID for your org).
Pull: summary, description (acceptance criteria / problem statement), issue type,
labels/components, and **linked issues** — a parent epic or sibling tickets are how
you discover an epic-across-PRs. Fetch the parent epic too when there is one; it often
holds the real problem statement. If the ticket is inaccessible, say so and continue
from the PR/branch alone (the brief is still useful; note the gap).

If the atlassian MCP is not connected in this session, don't fail: ask the user to
paste the ticket text, or proceed from the PR description and code, and note that the
Jira context is from the description only.

### 3. Read the actual change — code first, diff second

This is the step that separates a brief from a paraphrase. Do NOT flip the shared
working tree. Read the branch in an isolated worktree:

```bash
git fetch origin "$BRANCH"
git worktree add -f /tmp/brief_wt origin/"$BRANCH"   # detached, isolated copy
cd /tmp/brief_wt                                       # read from HERE
# ... when done, from the main repo:  git worktree remove /tmp/brief_wt --force
```

Then:
- Get the change surface: `git diff --stat master...origin/$BRANCH` (or `gh pr diff $PR --name-only`).
- For every new/renamed symbol, table, enum, node, endpoint — **open the full file**,
  not just the diff hunk, and trace it: who produces it, who reads it, what the old
  behaviour was. The example's citations (`playbook_dao.py:24`, `device_grouper.py:21`)
  come from reading those files, not from the diff.
- Confirm each claim in the PR/ticket description against the code. Note disagreements.
- For an epic, map each PR to its files and its purpose (`gh pr diff --name-only`).

Capture the concrete `file:line` anchors as you go — you will cite them in the brief.

### 4. Write the brief (markdown, default output)

Write `pr_brief_<TICKET>.md` (or `pr_brief_<BRANCH>.md` when there is no ticket) to
the repo root — pasteable into the PR description or a Jira comment, renders on GitHub.
Structure, following the example — omit any section that does not apply:

- **Title**: `TICKET — <one line: what it does and why>` (mirror the example's header).
- **Problem**: 2-4 sentences. The state of the world today and why it's inadequate.
  Ground it: cite the code that has the limitation.
- **Fix**: the high-level shape of the solution in plain prose.
- **Design sections** (as many as the change warrants), each a short titled prose
  block. This is the body. Cover the non-obvious decisions and for each give the
  *why*. Include a **"Key design"**-style section that names the rejected alternative
  and says why it was rejected, whenever the change deliberately departs from the
  existing pattern in the codebase.
- **Open decisions**: anything undecided, who owns it, and what changes once decided.
- **Data / control flow**: a short walkthrough of the end-to-end path when the change
  adds or reroutes one ("the user selects devices ... the researcher gives them to
  the writer").
- **Blast radius**: what this touches, which existing behaviours change, the scale /
  fan-out, and where the risk is concentrated. Be specific and quantify when you can.
- **PR breakdown** (only for an epic): one subsection per PR — its ticket, its files
  (with a phrase on each), and what it changes. See the example's `PR 1 … PR 4`.

Rules: prose over bullet-dumps; every design claim carries a `file:line`; English;
no em dashes; no invented facts — if you didn't verify it, don't assert it (say
"per the ticket" or omit). Match the example's register.

Clean up the worktree.

### 5. Render the HTML and open it

Always do this — the markdown is the source of truth, the HTML is the reading view,
and it gets it opened without asking. Generate a self-contained, styled
single-page document from the same content and open it:

```bash
python3 ~/.claude/skills/pr-brief/generate_brief_html.py \
  --md pr_brief_<TICKET>.md --out pr_brief_<TICKET>.html \
  --title "<TICKET> — <summary>"
open pr_brief_<TICKET>.html      # macOS; use xdg-open on Linux
```

The generator renders the markdown into a clean reading page with a light/dark toggle
and a sticky section nav. If `open` is unavailable (headless / Linux without a
browser), just report both paths instead.

Then show the user both paths and a short summary of what the brief covers.

## Not this

- Not a code review. No severities, no findings, no "you should fix". If you spot a
  real bug while reading, mention it once in a short "Worth a second look" line at the
  end — but the job is context, not judgement. For findings, use `pr-review-html`.
- Not a diff restatement. If a sentence would be obvious from reading the diff, cut it.
- Not a description copy. If the brief could have been written without opening the
  branch, it failed.
