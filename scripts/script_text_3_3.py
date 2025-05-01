#!/usr/bin/env python3
"""
Extractor → JSON using Kraken OCR only (pure‐Python API)
──────────────────────────────────────────────────────────────
Drop PDFs or images into ./input/ and run:

    python ocr_kraken_only.py

For each file you get in ./output/:
  - <name>_pages.json : [{"page":1,"text":"...","ocr_model":"kraken"}, …]

Requires:
  pip install kraken pymupdf pillow
"""
from __future__ import annotations
import json
from pathlib import Path

import fitz                            # PyMuPDF
from PIL import Image
import numpy as np
from kraken import binarization, pageseg, rpred

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR .mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

def ocr_kraken(img: Image.Image) -> str:
    """
    Run Kraken OCR on a PIL image, return the concatenated text.
    Uses the built-in 'en-default.handwritten' model.
    """
    # convert to grayscale numpy array
    gray = np.array(img.convert("L"))
    # binarize
    bin_img = binarization.nlbin(gray)
    # segment into line regions
    regions = pageseg.segment(bin_img)
    # run recognition
    records = rpred.rpred(bin_img, regions, model='en-default.handwritten')
    # join all line texts
    return " ".join(rec['text'] for rec in records)

def _write_json(pages: list[dict], out_path: Path) -> None:
    out_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")

def process_pdf(path: Path) -> None:
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = ocr_kraken(img)
        pages.append({"page": i, "text": text, "ocr_model": "kraken"})
    _write_json(pages, OUTPUT_DIR / f"{path.stem}_pages.json")
    print(f"✔ {path.name} → {path.stem}_pages.json")

def process_images(files: list[Path]) -> None:
    pages = []
    for i, f in enumerate(sorted(files), start=1):
        img = Image.open(f)
        text = ocr_kraken(img)
        pages.append({"page": i, "text": text, "ocr_model": "kraken"})
    _write_json(pages, OUTPUT_DIR / "images_pages.json")
    print("✔ images → images_pages.json")

def main() -> None:
    files = sorted(INPUT_DIR.iterdir())
    pdfs = [f for f in files if f.suffix.lower() == ".pdf"]
    imgs = [f for f in files if f.suffix.lower() in (".png",".jpg",".jpeg",".tiff",".bmp",".gif")]

    if not (pdfs or imgs):
        print("Drop PDFs or images into input/ and rerun.")
        return

    for pdf in pdfs:
        process_pdf(pdf)
    if imgs:
        process_images(imgs)

if __name__ == "__main__":
    main()
