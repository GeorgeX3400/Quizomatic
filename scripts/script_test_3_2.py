#!/usr/bin/env python3
"""
Extractor → JSON including both Tesseract & EasyOCR outputs, plus best‐pick tag
───────────────────────────────────────────────────────────────────────────────
Drop PDFs, DOCX or images into ./input/ and run:

    python pdf_layout_to_html.py

Output (./output/<name>_pages.json):
[
  {
    "page":1,
    "text_tesseract":"...",
    "text_easyocr":"...",
    "best_text":"...",
    "best_model":"easyocr_ro"
  },
  ...
]
"""
from __future__ import annotations
import json, re
from io import BytesIO
from pathlib import Path

import fitz                    # PyMuPDF
from PIL import Image
import pytesseract
from docx import Document
import easyocr
import numpy as np

# ── Config ─────────────────────────────────────────────────────
TESS_LANG = "ron"        # Romanian in Tesseract
# If needed:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
for d in (INPUT_DIR, OUTPUT_DIR):
    d.mkdir(exist_ok=True, parents=True)

# ── EasyOCR reader ────────────────────────────────────────────
reader = easyocr.Reader(["ro"], gpu=False)

# ── Helpers ───────────────────────────────────────────────────
def _clean(txt: str) -> str:
    txt = re.sub(r"[\r\n]+", " ", txt)
    txt = txt.replace("{", "").replace("}", "")
    return re.sub(r"\s{2,}", " ", txt).strip()

def letter_ratio(txt: str) -> float:
    total = len(txt)
    if total == 0:
        return 0.0
    letters = sum(c.isalpha() for c in txt)
    return letters / total

def _write_json(pages: list[dict], out_path: Path) -> None:
    out_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")

# ── OCR routines ───────────────────────────────────────────────
def ocr_tesseract(img: Image.Image) -> str:
    raw = pytesseract.image_to_string(img, lang=TESS_LANG)
    return _clean(raw)

def ocr_easyocr(img: Image.Image) -> str:
    arr = np.array(img)
    results = reader.readtext(arr)
    return _clean(" ".join([r[1] for r in results]))

def run_both(img: Image.Image) -> tuple[str,str,str,str]:
    """
    Returns:
      (tess_txt, easy_txt, best_txt, best_model)
    """
    tess = ocr_tesseract(img)
    easy = ocr_easyocr(img)
    score_t = letter_ratio(tess)
    score_e = letter_ratio(easy)
    if score_e > score_t:
        return tess, easy, easy, "easyocr_ro"
    else:
        return tess, easy, tess, "tesseract_ro"

# ── File processors ───────────────────────────────────────────
def process_pdf(path: Path):
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        tess, easy, best, model = run_both(img)
        pages.append({
            "page": i,
            "text_tesseract": tess,
            "text_easyocr": easy,
            "best_text": best,
            "best_model": model
        })
    _write_json(pages, OUTPUT_DIR / f"{path.stem}_pages.json")
    print(f"✔ {path.name} → {path.stem}_pages.json")

def process_docx(path: Path):
    doc = Document(path)
    full = _clean("\n".join(p.text for p in doc.paragraphs))
    pages = []
    if full.strip():
        tess, easy, best, model = full, "", full, "native"
    else:
        # force OCR on blank page
        blank = Image.new("RGB",(800,1000),"white")
        tess, easy, best, model = run_both(blank)
    pages.append({
        "page": 1,
        "text_tesseract": tess,
        "text_easyocr": easy,
        "best_text": best,
        "best_model": model
    })
    idx = 2
    for rel in doc.part.rels.values():
        if "image" not in rel.target_part.content_type:
            continue
        img = Image.open(BytesIO(rel.target_part.blob))
        tess, easy, best, model = run_both(img)
        pages.append({
            "page": idx,
            "text_tesseract": tess,
            "text_easyocr": easy,
            "best_text": best,
            "best_model": model
        })
        idx += 1
    _write_json(pages, OUTPUT_DIR / f"{path.stem}_pages.json")
    print(f"✔ {path.name} → {path.stem}_pages.json")

def process_images(files, prefix):
    pages = []
    for i, f in enumerate(sorted(files), start=1):
        img = Image.open(f)
        tess, easy, best, model = run_both(img)
        pages.append({
            "page": i,
            "text_tesseract": tess,
            "text_easyocr": easy,
            "best_text": best,
            "best_model": model
        })
    _write_json(pages, OUTPUT_DIR / f"{prefix}_pages.json")
    print(f"✔ {prefix} → {prefix}_pages.json")

# ── Main ──────────────────────────────────────────────────────
def main():
    files = sorted(INPUT_DIR.iterdir())
    imgs = [f for f in files if f.suffix.lower() in (".png",".jpg",".jpeg",".tiff",".bmp",".gif")]
    pdfs = [f for f in files if f.suffix.lower()==".pdf"]
    docs = [f for f in files if f.suffix.lower()==".docx"]

    if not (imgs or pdfs or docs):
        print("Drop PDFs, DOCX or images into input/ and rerun.")
        return

    if imgs:
        process_images(imgs, "images")
    for pdf in pdfs:
        process_pdf(pdf)
    for doc in docs:
        process_docx(doc)

if __name__=="__main__":
    main()
