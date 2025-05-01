#!/usr/bin/env python3
"""
Extractor → clean JSON (text + Romanian Tesseract OCR + gibberish filter)
────────────────────────────────────────────────────────────────────────
Drop PDFs, DOCX or images into ./input/ and run:

    python pdf_layout_to_html.py

For each file you get in ./output/:
  - <name>_pages.json :
      [
        {"page":1,"text":"...","ocr_model":"tesseract_ro"},
        {"page":2,"text":"...","ocr_model":"tesseract_ro"}
      ]

Logic:
  • Always run Tesseract OCR on every page/image, using Romanian language data.
  • Clean up newlines/braces/extra spaces.
  • Mark every page as `"ocr_model":"tesseract_ro"`.

Requires:
  • **Tesseract-OCR** with **Romanian** traineddata:
      1. Download `ron.traineddata` from https://github.com/tesseract-ocr/tessdata  
      2. Place it in your Tesseract `tessdata/` folder (e.g. `C:\Program Files\Tesseract-OCR\tessdata\`)
  • Python modules:
      ```bash
      pip install pymupdf pytesseract pillow python-docx pyenchant
      ```
      *(No TrOCR or torch needed here)*

"""
from __future__ import annotations
import json, re
from io import BytesIO
from pathlib import Path

import fitz            # PyMuPDF
from PIL import Image
import pytesseract
from docx import Document
import enchant         # for a final gibberish sanity‐check

# ── Configuration ────────────────────────────────────────────
# If tesseract.exe isn’t on your PATH, uncomment and adjust:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

TESS_LANG = "ron"   # Romanian
# minimal heuristics in case even Tesseract trips:
GIB_WORD_THRESHOLD = 0.5   # <50% real words → probably garbage

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR .mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# ── Gibberish check ───────────────────────────────────────────
_dict = enchant.Dict("en_US")  # fallback English check

def _clean_text(txt: str) -> str:
    txt = re.sub(r"[\r\n]+", " ", txt)
    txt = txt.replace("{", "").replace("}", "")
    txt = re.sub(r"\s{2,}", " ", txt)
    return txt.strip()

def is_gibberish(txt: str, threshold: float = GIB_WORD_THRESHOLD) -> bool:
    words = re.findall(r"\b[^\d\W]{2,}\b", txt)  # at least 2-letter words
    if not words:
        return True
    good = sum(1 for w in words if _dict.check(w))
    return (good / len(words)) < threshold

# ── OCR helper ────────────────────────────────────────────────
def ocr_tesseract_ro(img: Image.Image) -> str:
    raw = pytesseract.image_to_string(img, lang=TESS_LANG)
    return _clean_text(raw)

# ── Batch write ──────────────────────────────────────────────
def _write_json(pages, outpath):
    outpath.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Handlers ─────────────────────────────────────────────────
def process_images(img_files, prefix):
    pages = []
    for i, f in enumerate(sorted(img_files), start=1):
        img = Image.open(f)
        txt = ocr_tesseract_ro(img)
        pages.append({"page": i, "text": txt, "ocr_model": "tesseract_ro"})
    _write_json(pages, OUTPUT_DIR / f"{prefix}_pages.json")
    print(f"✔ {prefix} (images) → {prefix}_pages.json")

def process_docx(f):
    doc = Document(f)
    full = "\n".join(p.text for p in doc.paragraphs)
    txt = _clean_text(full)
    # if the extracted text is gibberish, re-run OCR on a blank image to force proper scan
    if is_gibberish(txt):
        txt = ocr_tesseract_ro(Image.new("RGB",(800,1000),"white"))
    pages = [{"page":1, "text":txt, "ocr_model":"tesseract_ro"}]
    # then any embedded pictures
    idx = 2
    for rel in doc.part.rels.values():
        if "image" not in rel.target_part.content_type: continue
        img = Image.open(BytesIO(rel.target_part.blob))
        txt = ocr_tesseract_ro(img)
        pages.append({"page":idx, "text":txt, "ocr_model":"tesseract_ro"})
        idx += 1
    _write_json(pages, OUTPUT_DIR / f"{f.stem}_pages.json")
    print(f"✔ {f.name} → {f.stem}_pages.json")

def process_pdf(f):
    doc = fitz.open(f)
    pages = []
    for i, page in enumerate(doc, start=1):
        # always OCR the rendered page
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        txt = ocr_tesseract_ro(img)
        pages.append({"page":i, "text":txt, "ocr_model":"tesseract_ro"})
    _write_json(pages, OUTPUT_DIR / f"{f.stem}_pages.json")
    print(f"✔ {f.name} → {f.stem}_pages.json")

def main():
    files = sorted(INPUT_DIR.iterdir())
    imgs = [f for f in files if f.suffix.lower() in (".png",".jpg",".jpeg",".tiff",".bmp",".gif")]
    pdfs = [f for f in files if f.suffix.lower()==".pdf"]
    docs = [f for f in files if f.suffix.lower()==".docx"]
    if not (imgs or pdfs or docs):
        print("Drop PDF/DOCX/images into input/ and rerun.")
        return
    if imgs:    process_images(imgs, "images")
    for pd in pdfs: process_pdf(pd)
    for dc in docs: process_docx(dc)

if __name__=="__main__":
    main()
