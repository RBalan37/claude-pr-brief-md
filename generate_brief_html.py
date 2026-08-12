#!/usr/bin/env python3
"""Render a PR brief markdown file into a self-contained, styled HTML page.

The brief markdown is the source of truth (see the pr-brief skill). This script
is a convenience view: one file, no network, no dependencies beyond the Python
standard library. It renders a clean reading page with a light/dark toggle and a
sticky section navigation built from the `##` headings.

Usage:
    python3 generate_brief_html.py --md pr_brief_AMVP-156149.md \
        --out pr_brief_AMVP-156149.html \
        [--title "AMVP-156149 — Store what we know about a device class"]

Supported markdown (a deliberately small subset — briefs use only these):
  # H1            page title (used if --title not given)
  ## H2 / ### H3  sections / subsections (H2 populate the side nav)
  - bullet        unordered list (contiguous items grouped into one <ul>)
  **bold**        <strong>
  `code`          <code>
  **Label:** ...  a leading bold label on a paragraph renders inline
  blank line      paragraph break
`file.py:123` spans are auto-tagged with a subtle monospace pill so the
reviewer's eye lands on the code anchors that make the brief trustworthy.
"""
