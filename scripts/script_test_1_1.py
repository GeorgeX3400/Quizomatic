#!/usr/bin/env python3
"""
PDF → layout-aware HTML + clean page-text JSON
──────────────────────────────────────────────
Drop any number of *.pdf* files into **input/** (same folder as this script)
and run:

    python pdf_layout_to_html.py

Outputs appear in **output/**:
• <name>.html          – preserves columns/tables visually
• <name>_pages.json    – list[{page, text}] with **no new-lines or “{ }” chars**

Tested: PyMuPDF 1.24+, Python 3.12 (Windows).   Install via:

    pip install pymupdf
"""
from __future__ import annotations
import json, re
from pathlib import Path
import fitz  # PyMuPDF

# ── Folder paths ──────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True,  parents=True)
INPUT_DIR.mkdir(exist_ok=True,   parents=True)   # so the user sees it

# ── Text-cleanup helpers ──────────────────────────────────────
def _clean_text(txt: str) -> str:
    """Flatten new-lines, strip curly braces, collapse whitespace."""
    txt = re.sub(r"[\r\n]+", " ", txt)          # new-lines → space
    txt = txt.replace("{", "").replace("}", "") # remove braces
    txt = re.sub(r"\s{2,}", " ", txt)           # multi-spaces → single
    return txt.strip()

def _post_process_json(json_path: Path) -> None:
    """Load the freshly-written JSON, clean each page’s text, overwrite."""
    pages = json.loads(json_path.read_text(encoding="utf-8"))
    for p in pages:
        p["text"] = _clean_text(p["text"])
    json_path.write_text(
        json.dumps(pages, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# ── Conversion core ──────────────────────────────────────────
def convert(pdf_path: Path, out_dir: Path) -> None:
    doc = fitz.open(pdf_path)
    html_parts: list[str] = []
    text_pages: list[dict[str, str | int]] = []

    for page_no, page in enumerate(doc, 1):
        html_parts.append(f"<div class='page' id='p{page_no}'>")
        html_parts.append(page.get_text("html", flags=fitz.TEXT_PRESERVE_LIGATURES))
        html_parts.append("</div>")
        text_pages.append({
            "page": page_no,
            "text": page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES)
        })

    html_file = out_dir / f"{pdf_path.stem}.html"
    json_file = out_dir / f"{pdf_path.stem}_pages.json"

    html_file.write_text(_wrap_html("\n".join(html_parts)), encoding="utf-8")
    json_file.write_text(
        json.dumps(text_pages, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    _post_process_json(json_file)     # ← cleanup pass

    print(f"✔ {pdf_path.name} → {html_file.name}, {json_file.name}")

def _wrap_html(body: str) -> str:
    """Minimal CSS so each page looks like a sheet of paper."""
    return (
        "<html><head><meta charset='utf-8'><style>"
        ".page{position:relative;margin:40px auto;border:1px solid #ddd;"
        "box-shadow:0 0 6px rgba(0,0,0,.15);padding:1em;width:fit-content;}"
        "span{position:absolute;white-space:pre;}"
        "body{background:#f5f5f5;font-family:Arial,Helvetica,sans-serif;}"
        "</style></head><body>" + body + "</body></html>"
    )

# ── Batch driver ─────────────────────────────────────────────
def main() -> None:
    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {INPUT_DIR} – drop PDFs there and rerun.")
        return
    for pdf in pdfs:
        convert(pdf, OUTPUT_DIR)

if __name__ == "__main__":
    main()
