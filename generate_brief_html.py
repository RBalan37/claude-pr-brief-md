#!/usr/bin/env python3
"""Render a PR brief markdown file into a self-contained HTML reading page."""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


def inline_markdown(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def markdown_to_html(md: str) -> tuple[str, list[tuple[str, str]]]:
    lines = md.splitlines()
    out: list[str] = []
    nav: list[tuple[str, str]] = []
    in_code = False
    in_ul = False
    in_ol = False
    code_lines: list[str] = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("```"):
            close_lists()
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            close_lists()
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            close_lists()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            anchor = slugify(title)
            if level <= 3:
                nav.append((anchor, title))
            out.append(
                f'<h{level} id="{anchor}">{inline_markdown(title)}</h{level}>'
            )
            continue

        ul = re.match(r"^[-*]\s+(.*)$", line)
        if ul:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline_markdown(ul.group(1))}</li>")
            continue

        ol = re.match(r"^\d+\.\s+(.*)$", line)
        if ol:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline_markdown(ol.group(1))}</li>")
            continue

        close_lists()
        out.append(f"<p>{inline_markdown(line)}</p>")

    if in_code and code_lines:
        out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    close_lists()
    return "\n".join(out), nav


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #fafafa;
      --surface: #ffffff;
      --text: #1a1a1a;
      --muted: #666;
      --border: #e5e5e5;
      --accent: #2563eb;
      --code-bg: #f4f4f5;
    }}
    [data-theme="dark"] {{
      --bg: #0f1117;
      --surface: #171923;
      --text: #e8eaed;
      --muted: #9aa0a6;
      --border: #2d3142;
      --accent: #60a5fa;
      --code-bg: #1e2230;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.65;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 240px minmax(0, 760px);
      gap: 2rem;
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 1.5rem 4rem;
    }}
    nav {{
      position: sticky;
      top: 1.5rem;
      align-self: start;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem;
      max-height: calc(100vh - 3rem);
      overflow: auto;
    }}
    nav h2 {{
      margin: 0 0 0.75rem;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    nav a {{
      display: block;
      color: var(--muted);
      text-decoration: none;
      font-size: 0.9rem;
      padding: 0.25rem 0;
    }}
    nav a:hover {{ color: var(--accent); }}
    main {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 2rem 2.25rem;
    }}
    .toolbar {{
      display: flex;
      justify-content: flex-end;
      margin-bottom: 1rem;
    }}
    button {{
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      border-radius: 8px;
      padding: 0.4rem 0.75rem;
      cursor: pointer;
      font-size: 0.85rem;
    }}
    h1 {{ font-size: 1.75rem; margin-top: 0; line-height: 1.25; }}
    h2 {{ font-size: 1.25rem; margin-top: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 0.35rem; }}
    h3 {{ font-size: 1.05rem; margin-top: 1.5rem; }}
    p {{ margin: 0.85rem 0; }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.9em;
      background: var(--code-bg);
      padding: 0.12rem 0.35rem;
      border-radius: 4px;
    }}
    pre {{
      background: var(--code-bg);
      border-radius: 8px;
      padding: 1rem;
      overflow: auto;
    }}
    pre code {{ background: none; padding: 0; }}
    a {{ color: var(--accent); }}
    @media (max-width: 860px) {{
      .layout {{ grid-template-columns: 1fr; }}
      nav {{ position: static; max-height: none; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <nav>
      <h2>Sections</h2>
      {nav_links}
    </nav>
    <main>
      <div class="toolbar">
        <button type="button" id="theme-toggle" aria-label="Toggle theme">Toggle theme</button>
      </div>
      {content}
    </main>
  </div>
  <script>
    const root = document.documentElement;
    const stored = localStorage.getItem('pr-brief-theme');
    if (stored === 'dark') root.setAttribute('data-theme', 'dark');
    document.getElementById('theme-toggle').addEventListener('click', () => {{
      const dark = root.getAttribute('data-theme') === 'dark';
      if (dark) {{
        root.removeAttribute('data-theme');
        localStorage.setItem('pr-brief-theme', 'light');
      }} else {{
        root.setAttribute('data-theme', 'dark');
        localStorage.setItem('pr-brief-theme', 'dark');
      }}
    }});
  </script>
</body>
</html>
"""


def build_nav(sections: list[tuple[str, str]]) -> str:
    if not sections:
        return "<p>No sections</p>"
    return "\n".join(
        f'<a href="#{anchor}">{html.escape(title)}</a>' for anchor, title in sections
    )


def render(md_path: Path, out_path: Path, title: str) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    content, nav = markdown_to_html(md_text)
    html_doc = HTML_TEMPLATE.format(
        title=html.escape(title),
        nav_links=build_nav(nav),
        content=content,
    )
    out_path.write_text(html_doc, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a PR brief markdown file to HTML.")
    parser.add_argument("--md", required=True, type=Path, help="Input markdown file")
    parser.add_argument("--out", required=True, type=Path, help="Output HTML file")
    parser.add_argument("--title", required=True, help="HTML page title")
    args = parser.parse_args()

    if not args.md.is_file():
        print(f"error: markdown file not found: {args.md}", file=sys.stderr)
        return 1

    render(args.md, args.out, args.title)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
