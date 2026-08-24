#!/usr/bin/env python3
"""Render a PR brief markdown file into a self-contained, styled HTML page.

The brief markdown is the source of truth (see the pr-brief skill). This script
is a convenience view: one file, no network, no dependencies beyond the Python
standard library. It renders a clean reading page with a light/dark toggle and a
sticky section navigation built from the `##` headings.

Usage:
    python3 generate_brief_html.py --md pr_brief_ACC-214.md \
        --out pr_brief_ACC-214.html \
        [--title "ACC-214 — Soft-delete user accounts with a recovery window"]

Supported markdown (a deliberately small subset — briefs use only these):
  # H1            page title (used if --title not given)
  ## H2 / ### H3  sections / subsections (H2 populate the side nav)
  - bullet        unordered list (contiguous items grouped into one <ul>)
  **bold**        <strong>
  `code`          <code>
  | a | b |       GitHub-style table (header + `---` separator row)
  ```             fenced code block (used for the data/control-flow diagrams)
  ---             horizontal rule (section divider)
  blank line      paragraph break
`file.py:123` spans (a backtick span matching `path:line` or `path:line-line`)
are auto-tagged with a subtle monospace pill so the reviewer's eye lands on the
code anchors that make the brief trustworthy.
"""

import argparse
import html
import re
import sys

LOC_RE = re.compile(r"^[\w./-]+\.\w+:\d+(-\d+)?$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")
SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text):
    slug = SLUG_RE.sub("-", text.strip().lower()).strip("-")
    return slug or "section"


def render_inline(text):
    """Escape then apply inline markdown: code spans (with file:line pills), bold."""
    escaped = html.escape(text, quote=False)

    def code_sub(match):
        content = match.group(1)
        cls = "loc" if LOC_RE.match(content) else "code"
        return f'<code class="{cls}">{content}</code>'

    with_code = CODE_RE.sub(code_sub, escaped)
    return BOLD_RE.sub(r"<strong>\1</strong>", with_code)


def render_markdown(md_text):
    """Parse the small markdown subset into (title, nav_items, body_html)."""
    lines = md_text.splitlines()
    title = None
    nav_items = []  # list of (id, text)
    body = []
    paragraph = []
    list_items = []
    i = 0
    n = len(lines)

    def flush_paragraph():
        if paragraph:
            body.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list():
        if list_items:
            items = "".join(f"<li>{render_inline(item)}</li>" for item in list_items)
            body.append(f"<ul>{items}</ul>")
            list_items.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            i += 1
            code_lines = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            code_text = html.escape("\n".join(code_lines), quote=False)
            body.append(f"<pre><code>{code_text}</code></pre>")
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            flush_list()
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            body.append(render_table(table_lines))
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            i += 1
            continue

        if re.fullmatch(r"-{3,}", stripped):
            flush_paragraph()
            flush_list()
            body.append("<hr>")
            i += 1
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            heading = stripped[2:].strip()
            if title is None:
                title = heading
            body.append(f"<h1>{render_inline(heading)}</h1>")
            i += 1
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            heading = stripped[3:].strip()
            section_id = slugify(heading)
            nav_items.append((section_id, heading))
            body.append(f'<h2 id="{section_id}">{render_inline(heading)}</h2>')
            i += 1
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            flush_list()
            heading = stripped[4:].strip()
            body.append(f"<h3>{render_inline(heading)}</h3>")
            i += 1
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            list_items.append(stripped[2:].strip())
            i += 1
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    flush_list()
    return title, nav_items, "\n".join(body)


def render_table(table_lines):
    def split_row(row):
        return [cell.strip() for cell in row.strip("|").split("|")]

    header = split_row(table_lines[0])
    data_rows = [split_row(r) for r in table_lines[2:]] if len(table_lines) > 1 else []

    thead = "".join(f"<th>{render_inline(cell)}</th>" for cell in header)
    tbody = "".join(
        "<tr>" + "".join(f"<td>{render_inline(cell)}</td>" for cell in row) + "</tr>"
        for row in data_rows
    )
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>"


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg: #ffffff; --fg: #1a1a1a; --muted: #5f6368; --border: #e2e2e2;
    --code-bg: #f2f2f2; --pill-bg: #eef2ff; --pill-fg: #3730a3; --accent: #2563eb;
  }}
  [data-theme="dark"] {{
    --bg: #14161a; --fg: #e6e6e6; --muted: #9aa0a6; --border: #2c2f36;
    --code-bg: #1e2126; --pill-bg: #232a4d; --pill-fg: #b3c0ff; --accent: #7aa2ff;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--fg);
    font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}
  .layout {{ display: flex; max-width: 1100px; margin: 0 auto; }}
  nav {{
    position: sticky; top: 0; align-self: flex-start; height: 100vh;
    overflow-y: auto; width: 220px; flex: 0 0 220px; padding: 24px 12px;
    border-right: 1px solid var(--border);
  }}
  nav a {{
    display: block; padding: 6px 10px; color: var(--muted); text-decoration: none;
    border-radius: 6px; font-size: 14px;
  }}
  nav a:hover {{ background: var(--code-bg); color: var(--fg); }}
  main {{ flex: 1; min-width: 0; padding: 32px 40px 80px; }}
  h1 {{ font-size: 1.6em; margin: 0 0 8px; }}
  h2 {{ font-size: 1.25em; margin-top: 2em; border-top: 1px solid var(--border); padding-top: 1em; }}
  h3 {{ font-size: 1.05em; }}
  p {{ margin: 0.8em 0; }}
  ul {{ padding-left: 1.4em; }}
  li {{ margin: 0.3em 0; }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 2em 0; }}
  code {{ background: var(--code-bg); padding: 0.1em 0.35em; border-radius: 4px; font-size: 0.9em; }}
  code.loc {{
    background: var(--pill-bg); color: var(--pill-fg); font-family: "SF Mono", Menlo, monospace;
  }}
  pre {{
    background: var(--code-bg); padding: 16px; border-radius: 8px; overflow-x: auto;
  }}
  pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
  th, td {{ border: 1px solid var(--border); padding: 8px 10px; text-align: left; font-size: 0.95em; }}
  th {{ background: var(--code-bg); }}
  #theme-toggle {{
    position: fixed; top: 16px; right: 16px; border: 1px solid var(--border);
    background: var(--bg); color: var(--fg); border-radius: 6px; padding: 6px 10px;
    cursor: pointer; font-size: 13px;
  }}
</style>
</head>
<body>
<button id="theme-toggle" onclick="toggleTheme()">Toggle theme</button>
<div class="layout">
  <nav>{nav}</nav>
  <main>{body}</main>
</div>
<script>
  function applyTheme(theme) {{
    document.documentElement.setAttribute('data-theme', theme);
  }}
  (function () {{
    var saved = null;
    try {{ saved = localStorage.getItem('pr-brief-theme'); }} catch (e) {{}}
    if (saved) {{
      applyTheme(saved);
    }} else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
      applyTheme('dark');
    }}
  }})();
  function toggleTheme() {{
    var current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    try {{ localStorage.setItem('pr-brief-theme', next); }} catch (e) {{}}
  }}
</script>
</body>
</html>
"""


def build_html(md_text, title_override):
    parsed_title, nav_items, body_html = render_markdown(md_text)
    title = title_override or parsed_title or "PR Brief"
    nav_html = "".join(f'<a href="#{sid}">{html.escape(text, quote=False)}</a>' for sid, text in nav_items)
    return PAGE_TEMPLATE.format(title=html.escape(title, quote=False), nav=nav_html, body=body_html)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--md", required=True, help="Path to the brief markdown file")
    parser.add_argument("--out", required=True, help="Path to write the rendered HTML file")
    parser.add_argument("--title", default=None, help="Page title (defaults to the markdown's H1)")
    args = parser.parse_args()

    try:
        with open(args.md, "r", encoding="utf-8") as f:
            md_text = f.read()
    except OSError as e:
        print(f"Error reading {args.md}: {e}", file=sys.stderr)
        sys.exit(1)

    html_out = build_html(md_text, args.title)

    try:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(html_out)
    except OSError as e:
        print(f"Error writing {args.out}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
