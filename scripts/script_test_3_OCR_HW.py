#!/usr/bin/env python3
"""
Universal extractor → clean JSON (text + hybrid OCR + gibberish & layout checks + model tag)
───────────────────────────────────────────────────────────────────────────────────────────
Drop PDFs, DOCX or images into ./input/ and run:

    python pdf_layout_to_html.py

For each file you get in ./output/:
  - <name>_pages.json :
      [
        {"page":1,"text":"...","ocr_model":"native"},
        {"page":2,"text":"...","ocr_model":"trocr"}
      ]

Logic:
  • Try native text layer first (via PyMuPDF / python-docx)
  • If native layer is empty, too short, gibberish, or low letter‐ratio → hybrid OCR:
       – Tesseract first (fast)  
       – If Tesseract conf <60% or output <20 chars or gibberish → TrOCR (handwriting)

Requires:
  • Tesseract-OCR engine on your system  
  • Python modules:
      pip install pymupdf pytesseract pillow python-docx transformers torch torchvision pyenchant
"""
from __future__ import annotations
import json, re
from io import BytesIO
from pathlib import Path

import fitz                            # PyMuPDF
from PIL import Image
import pytesseract
from pytesseract import Output
from docx import Document
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import enchant                         # for gibberish detection

# ── Configuration ────────────────────────────────────────────
# Uncomment & adjust if needed:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

TESS_CONF_THRESHOLD     = 60.0     # Tesseract mean confidence % below → fallback
TESS_LEN_THRESHOLD      = 20       # Tesseract output length below → fallback
GIB_WORD_THRESHOLD      = 0.5      # <50% real words → fallback
LETTER_RATIO_THRESHOLD  = 0.6      # <60% letters in native layer → fallback

# ── Load TrOCR once ───────────────────────────────────────────
_trocr_proc = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
_trocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
_trocr_model.eval()
if torch.cuda.is_available():
    _trocr_model.to("cuda")

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR .mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# ── Gibberish & layout checks ────────────────────────────────
_dict = enchant.Dict("en_US")

def _clean_text(txt: str) -> str:
    txt = re.sub(r"[\r\n]+", " ", txt)
    txt = txt.replace("{", "").replace("}", "")
    txt = re.sub(r"\s{2,}", " ", txt)
    return txt.strip()

def is_gibberish(txt: str, threshold: float = GIB_WORD_THRESHOLD) -> bool:
    words = re.findall(r"\b[a-zA-Z']+\b", txt)
    if not words:
        return True
    good = sum(1 for w in words if _dict.check(w))
    return (good / len(words)) < threshold

def letter_ratio(txt: str) -> float:
    total = len(txt)
    if total == 0:
        return 0.0
    letters = sum(1 for c in txt if c.isalpha())
    return letters / total

# ── OCR helpers ──────────────────────────────────────────────
def ocr_tesseract_with_conf(img: Image.Image) -> tuple[str, float]:
    data = pytesseract.image_to_data(img, output_type=Output.DICT)
    texts, confs = data["text"], data["conf"]
    valid: list[tuple[str,int]] = []
    for t, c in zip(texts, confs):
        if not t.strip():
            continue
        # c may already be int or str
        try:
            ci = int(c)
        except Exception:
            continue
        valid.append((t, ci))
    if not valid:
        return "", 0.0
    mean_conf = sum(ci for _, ci in valid) / len(valid)
    text = " ".join(t for t, _ in valid)
    return text, mean_conf

def ocr_trocr(img: Image.Image) -> str:
    if img.mode != "RGB":
        img = img.convert("RGB")
    inputs = _trocr_proc(images=img, return_tensors="pt").pixel_values
    if torch.cuda.is_available():
        inputs = inputs.to("cuda")
    out_ids = _trocr_model.generate(inputs, max_length=512, num_beams=4)
    return _trocr_proc.batch_decode(out_ids, skip_special_tokens=True)[0]

def hybrid_ocr(img: Image.Image) -> tuple[str, str]:
    """
    Returns (clean_text, model_used), where model_used is 'tesseract' or 'trocr'.
    """
    txt, conf = ocr_tesseract_with_conf(img)
    if conf < TESS_CONF_THRESHOLD or len(txt) < TESS_LEN_THRESHOLD or is_gibberish(txt):
        res = _clean_text(ocr_trocr(img))
        return res, "trocr"
    return _clean_text(txt), "tesseract"

# ── File processors ───────────────────────────────────────────
def process_images(image_paths: list[Path], out_prefix: str) -> None:
    pages = []
    for i, img_path in enumerate(sorted(image_paths), start=1):
        pil = Image.open(img_path)
        txt, model = hybrid_ocr(pil)
        pages.append({"page": i, "text": txt, "ocr_model": model})
    (OUTPUT_DIR / f"{out_prefix}_pages.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ {out_prefix} (images) → {out_prefix}_pages.json")

def process_docx(path: Path) -> None:
    doc = Document(path)
    full = "\n".join(p.text for p in doc.paragraphs)
    native = _clean_text(full)
    # Decide native vs fallback based on same criteria
    use_native = (
        native and
        len(native) >= TESS_LEN_THRESHOLD and
        not is_gibberish(native) and
        letter_ratio(native) >= LETTER_RATIO_THRESHOLD
    )
    pages = []
    if use_native:
        pages.append({"page": 1, "text": native, "ocr_model": "native"})
    else:
        # render dummy white image to force hybrid OCR
        img = Image.new("RGB", (800, 1000), "white")
        txt, model = hybrid_ocr(img)
        pages.append({"page": 1, "text": txt, "ocr_model": model})

    # embedded images
    idx = 2
    for rel in doc.part.rels.values():
        if "image" not in rel.target_part.content_type:
            continue
        img = Image.open(BytesIO(rel.target_part.blob))
        txt, model = hybrid_ocr(img)
        pages.append({"page": idx, "text": txt, "ocr_model": model})
        idx += 1

    (OUTPUT_DIR / f"{path.stem}_pages.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ {path.name} → {path.stem}_pages.json")

def process_pdf(path: Path) -> None:
    doc = fitz.open(path)
    pages = []
    for pgno, page in enumerate(doc, start=1):
        raw = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES).strip()
        ok = (
            raw and
            len(raw) >= TESS_LEN_THRESHOLD and
            not is_gibberish(_clean_text(raw)) and
            letter_ratio(_clean_text(raw)) >= LETTER_RATIO_THRESHOLD
        )
        if not ok:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            txt, model = hybrid_ocr(img)
        else:
            txt, model = _clean_text(raw), "native"
        pages.append({"page": pgno, "text": txt, "ocr_model": model})
    (OUTPUT_DIR / f"{path.stem}_pages.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ {path.name} → {path.stem}_pages.json")

# ── Main dispatch ─────────────────────────────────────────────
def main() -> None:
    files = sorted(INPUT_DIR.iterdir())
    imgs = [f for f in files if f.suffix.lower() in (".png",".jpg",".jpeg",".tiff",".bmp",".gif")]
    pdfs = [f for f in files if f.suffix.lower() == ".pdf"]
    docs = [f for f in files if f.suffix.lower() == ".docx"]
    if not (imgs or pdfs or docs):
        print("No supported files in input/. Drop images, PDFs or DOCX there.")
        return
    if imgs:
        process_images(imgs, "images")
    for pdf in pdfs:
        process_pdf(pdf)
    for doc in docs:
        process_docx(doc)

if __name__ == "__main__":
    main()
