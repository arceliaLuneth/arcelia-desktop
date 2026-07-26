from __future__ import annotations

import re
from typing import Dict, Tuple

import markdown as md
from pygments.formatters import HtmlFormatter

_FORMATTER = HtmlFormatter(style="monokai", nowrap=False)
_PYGMENTS_CSS = _FORMATTER.get_style_defs(".codehilite")

_BASE_CSS = f"""
body {{
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    color: #eef4fb;
    background: transparent;
}}
p {{ margin: 4px 0; }}
h1, h2, h3, h4 {{ margin: 10px 0 6px 0; color: #f5f8fc; }}
ul, ol {{ margin: 4px 0 4px 20px; }}
code {{
    background: #1c2636;
    padding: 2px 5px;
    border-radius: 4px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
}}
pre {{
    background: #12192a;
    border: 1px solid #223044;
    border-radius: 10px;
    padding: 10px;
    overflow-x: auto;
}}
pre code {{ background: transparent; padding: 0; }}
.codehilite {{
    background: #12192a;
    border: 1px solid #223044;
    border-radius: 10px;
    padding: 2px 2px 0 2px;
    margin: 6px 0;
}}
.codehilite pre {{ border: none; margin: 0; }}
table {{ border-collapse: collapse; margin: 8px 0; }}
th, td {{ border: 1px solid #2a3a52; padding: 4px 8px; }}
a.copy-link {{
    display: inline-block;
    color: #86a6ff;
    font-size: 11px;
    text-decoration: none;
    padding: 4px 8px 8px 8px;
}}
{_PYGMENTS_CSS}
"""

_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_CODEHILITE_RE = re.compile(
    r'(<div class="codehilite"><pre>.*?</pre>)(</div>)', re.DOTALL
)


def _extract_raw_code_blocks(text: str) -> Dict[str, str]:
    blocks: Dict[str, str] = {}
    for i, match in enumerate(_FENCE_RE.finditer(text), start=1):
        blocks[str(i)] = match.group(1)
    return blocks


def _insert_copy_links(html_body: str) -> str:
    counter = {"n": 0}

    # Insert a "Copy code" link right after each highlighted block so it
    # renders as a small caption beneath the code.
    def repl_after(match: "re.Match[str]") -> str:
        counter["n"] += 1
        block_id = str(counter["n"])
        copy_link = f'<a class="copy-link" href="copy:{block_id}">Copy code</a>'
        return match.group(1) + match.group(2) + f"<div>{copy_link}</div>"

    return _CODEHILITE_RE.sub(repl_after, html_body)


def render_markdown(text: str) -> Tuple[str, Dict[str, str]]:
    """Render markdown text (with fenced code blocks) to styled HTML.

    Returns (full_html, code_blocks) where code_blocks maps the id used in
    'copy:<id>' anchor links to the raw, unhighlighted code so it can be
    copied to the clipboard verbatim.
    """
    code_blocks = _extract_raw_code_blocks(text)

    html_body = md.markdown(
        text,
        extensions=["fenced_code", "codehilite", "tables", "sane_lists", "nl2br"],
        extension_configs={
            "codehilite": {"guess_lang": True, "noclasses": False, "linenums": False}
        },
    )
    html_body = _insert_copy_links(html_body)

    return f"<html><head><style>{_BASE_CSS}</style></head><body>{html_body}</body></html>", code_blocks
