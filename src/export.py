import hashlib, json
from pathlib import Path
import pandas as pd
from schema import write_jsonl

PDF_PATH = "data/rendered/AAPL_10K_20250927.pdf"
DOC_ID = "0000320193-25-000079"
COMPANY, CIK = "Apple Inc.", "0000320193"

sha256 = hashlib.sha256(Path(PDF_PATH).read_bytes()).hexdigest()

def load_words_by_page(words_jsonl_path):
    """Load word-level records and group them by page number."""
    by_page = {}
    with open(words_jsonl_path, encoding="utf-8") as f:
        for line in f:
            w = json.loads(line)
            by_page.setdefault(w["page"], []).append(w)
    return by_page

def union_bbox(words):
    """Smallest rectangle containing every word's bbox."""
    if not words:
        return [0.0, 0.0, 612.0, 792.0]  # fallback: full US Letter page
    x0 = min(w["bbox"][0] for w in words)
    top = min(w["bbox"][1] for w in words)
    x1 = max(w["bbox"][2] for w in words)
    bottom = max(w["bbox"][3] for w in words)
    return [x0, top, x1, bottom]

words_by_page = load_words_by_page("data/parsed/AAPL_10K_20250927.words.jsonl")

records = []

for page_no in [1, 2, 3]:
    txt_path = Path(f"data/parsed/AAPL_10K_20250927_p{page_no:04d}.txt")
    if not txt_path.exists():
        continue
    text = txt_path.read_text(encoding="utf-8")
    if not text.strip():
        continue

    page_words = words_by_page.get(page_no, [])
    bbox = union_bbox(page_words)

    records.append({
        "doc_id": DOC_ID, "company": COMPANY, "cik": CIK,
        "form": "10-K", "fiscal_year": 2025, "fiscal_period": "FY",
        "page": page_no, "section": None,
        "block_id": f"p{page_no:04d}_b001", "block_type": "Text",
        "bbox": bbox,
        "text": text,
        "extractor": "pdfplumber", "extractor_version": "0.11",
        "ocr": False,
        "source_path": PDF_PATH, "sha256": sha256,
    })

table_csv = Path("data/tables/p32_stream_0.csv")
if table_csv.exists():
    df = pd.read_csv(table_csv, header=None)
    records.append({
        "doc_id": DOC_ID, "company": COMPANY, "cik": CIK,
        "form": "10-K", "fiscal_year": 2025, "fiscal_period": "FY",
        "page": 32, "section": "Item 8. Financial Statements",
        "block_id": "p0032_b001", "block_type": "Table",
        "bbox": [40.0, 100.0, 570.0, 400.0],  # still a placeholder — Camelot's report doesn't give us word-level bboxes directly
        "table": {
            "columns": [str(c) for c in df.columns],
            "rows": df.values.tolist(),
            "raw_cells": True,
        },
        "extractor": "camelot-stream", "extractor_version": "camelot-py",
        "ocr": False,
        "source_path": PDF_PATH, "sha256": sha256,
    })

Path("data/export").mkdir(parents=True, exist_ok=True)
write_jsonl(records, "data/export/AAPL_10K_20250927.jsonl")
print(f"wrote {len(records)} validated records")