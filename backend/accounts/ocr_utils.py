# backend/ocr_utils.py

import re
import json
from io import BytesIO
from pathlib import Path
from datetime import datetime

import fitz             # pip install pymupdf
from PIL import Image   # pip install pillow
import pytesseract      # pip install pytesseract
from docx import Document as DocxDocument  # pip install python-docx
import enchant          # pip install pyenchant

# ── CONFIGURATION ──────────────────────────────────────────────────────────

# Make sure "ron.traineddata" is installed in your Tesseract tessdata folder.
# If tesseract binary is not on your PATH, uncomment and point below:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

TESS_LANG = "ron"
GIB_WORD_THRESHOLD = 0.5  # <50% real words → consider text gibberish

# A simple English dictionary fallback (used to flag gibberish)
_dict = enchant.Dict("en_US")

# ── HELPERS ────────────────────────────────────────────────────────────────

def _clean_text(txt: str) -> str:
    """Remove newlines, braces, and collapse multiple spaces."""
    txt = re.sub(r"[\r\n]+", " ", txt)
    txt = txt.replace("{", "").replace("}", "")
    txt = re.sub(r"\s{2,}", " ", txt)
    return txt.strip()

def is_gibberish(txt: str, threshold: float = GIB_WORD_THRESHOLD) -> bool:
    """
    Heuristic: if fewer than threshold fraction of words are valid English,
    treat as gibberish (useful to catch bad DOCX‐only text).
    """
    words = re.findall(r"\b[^\d\W]{2,}\b", txt)  # at least 2-letter words
    if not words:
        return True
    good = sum(1 for w in words if _dict.check(w))
    return (good / len(words)) < threshold

def ocr_tesseract_ro(img: Image.Image) -> str:
    """Perform Tesseract→Romanian OCR on a PIL Image, then clean text."""
    raw = pytesseract.image_to_string(img, lang=TESS_LANG)
    return _clean_text(raw)

def extract_pages_from_pdf(filepath: Path) -> list[dict]:
    pages = []
    doc = fitz.open(str(filepath))
    for i, page in enumerate(doc, start=1):
        # Always render and OCR (to ensure Romanian language)
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        txt = ocr_tesseract_ro(img)
        pages.append({"page": i, "text": txt, "ocr_model": "tesseract_ro"})
    return pages

def extract_pages_from_docx(filepath: Path) -> list[dict]:
    pages = []
    doc = DocxDocument(str(filepath))

    # 1) Extract straight text from all paragraphs
    full = "\n".join(p.text for p in doc.paragraphs)
    txt = _clean_text(full)

    # If the extracted DOCX text seems like gibberish, do a “blank‐page OCR” fallback
    if is_gibberish(txt):
        # Create a blank white image and run OCR on that (to force Romanian word shapes)
        blank = Image.new("RGB", (800, 1000), "white")
        txt = ocr_tesseract_ro(blank)

    pages.append({"page": 1, "text": txt, "ocr_model": "tesseract_ro"})

    # 2) For each embedded image in the DOCX, run OCR on that image as a separate page
    idx = 2
    for rel in doc.part.rels.values():
        if "image" not in rel.target_part.content_type:
            continue
        blob = rel.target_part.blob
        img = Image.open(BytesIO(blob))
        ocr_text = ocr_tesseract_ro(img)
        pages.append({"page": idx, "text": ocr_text, "ocr_model": "tesseract_ro"})
        idx += 1

    return pages

def extract_pages_from_image(filepath: Path) -> list[dict]:
    img = Image.open(str(filepath))
    txt = ocr_tesseract_ro(img)
    return [{"page": 1, "text": txt, "ocr_model": "tesseract_ro"}]

def extract_pages(filepath: str) -> list[dict]:
    """
    Dispatch based on extension. Returns a list of dicts:
        [ { "page": 1, "text": "...", "ocr_model": "tesseract_ro" }, … ]
    """
    path = Path(filepath)
    suffix = path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"):
        return extract_pages_from_image(path)
    elif suffix == ".pdf":
        return extract_pages_from_pdf(path)
    elif suffix == ".docx":
        return extract_pages_from_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

def write_json_pages(pages: list[dict], outpath: Path) -> None:
    """
    Write the `pages` list as JSON to disk at `outpath`.
    """
    outpath.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
