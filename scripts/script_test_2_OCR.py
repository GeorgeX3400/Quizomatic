#!/usr/bin/env python3
"""
Universal extractor → clean JSON (text + OCR)
───────────────────────────────────────────────
Drop PDFs, DOCX or images into ./input/ and run:

    python pdf_layout_to_html.py

For each file you get in ./output/:
  - name_pages.json : [{"page":1,"text":"..."}, …]

Requires:
    pip install pymupdf pytesseract pillow python-docx
Also install tesseract-ocr on your OS (e.g. `apt install tesseract-ocr` or Homebrew).
"""
from __future__ import annotations
import json, re
from io import BytesIO
from pathlib import Path

import fitz                            # PyMuPDF
from PIL import Image
import pytesseract
from docx import Document

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR .mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# ── Cleaning helper ────────────────────────────────────────────────────
def _clean_text(txt: str) -> str:
    txt = re.sub(r"[\r\n]+", " ", txt)
    txt = txt.replace("{", "").replace("}", "")
    txt = re.sub(r"\s{2,}", " ", txt)
    return txt.strip()

def _write_json(stubs: list[dict], out_path: Path) -> None:
    out_path.write_text(
        json.dumps(stubs, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# ── OCR single image ───────────────────────────────────────────────────
def ocr_image(img: Image.Image) -> str:
    return pytesseract.image_to_string(img)

# ── Process standalone image files ────────────────────────────────────
def process_images(image_paths: list[Path], out_prefix: str) -> None:
    pages = []
    for i, img_path in enumerate(sorted(image_paths), start=1):
        img = Image.open(img_path)
        text = ocr_image(img)
        pages.append({ "page": i, "text": _clean_text(text) })
    _write_json(pages, OUTPUT_DIR / f"{out_prefix}_pages.json")
    print(f"✔ {out_prefix} (images) → {out_prefix}_pages.json")

# ── Process DOCX: text + embedded images ───────────────────────────────
def process_docx(path: Path) -> None:
    doc = Document(path)
    # 1) full-text as page 1
    full = "\n".join(p.text for p in doc.paragraphs)
    pages = [{ "page": 1, "text": _clean_text(full) }]
    # 2) now any images
    rels = doc.part.rels
    img_rels = [r for r in rels.values() if "image" in r.target_part.content_type]
    for idx, rel in enumerate(img_rels, start=2):
        blob = rel.target_part.blob
        img  = Image.open(BytesIO(blob))
        pages.append({ "page": idx, "text": _clean_text(ocr_image(img)) })
    _write_json(pages, OUTPUT_DIR / f"{path.stem}_pages.json")
    print(f"✔ {path.name} → {path.stem}_pages.json")

# ── Process PDF: text or OCR fallback ─────────────────────────────────
def process_pdf(path: Path) -> None:
    doc   = fitz.open(path)
    pages = []
    for pgno, page in enumerate(doc, start=1):
        txt = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES).strip()
        if not txt or len(txt) < 20:
            # likely scanned/image page → render & OCR
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            txt = ocr_image(img)
        pages.append({ "page": pgno, "text": _clean_text(txt) })
    _write_json(pages, OUTPUT_DIR / f"{path.stem}_pages.json")
    print(f"✔ {path.name} → {path.stem}_pages.json")

# ── Main: dispatch by extension ────────────────────────────────────────
def main() -> None:
    files = sorted(INPUT_DIR.iterdir())
    imgs  = [f for f in files if f.suffix.lower() in (".png",".jpg",".jpeg",".tiff",".bmp",".gif")]
    pdfs  = [f for f in files if f.suffix.lower() == ".pdf"]
    docs  = [f for f in files if f.suffix.lower() in (".docx",)]

    if not (imgs or pdfs or docs):
        print("No supported files in input/.  Drop images, PDFs or DOCX there.")
        return

    if imgs:
        process_images(imgs, "images")

    for pdf in pdfs:
        process_pdf(pdf)

    for doc in docs:
        process_docx(doc)

if __name__ == "__main__":
    main()
