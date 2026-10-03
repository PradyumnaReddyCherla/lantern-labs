import json, re, pdfplumber
from pathlib import Path
from ocr_fallback import ocr_page

N_MIN = 50        # min chars before we call a page "empty"
JUNK_RATIO = 0.3   # share of junk tokens before we call it "garbled"

CID_RE = re.compile(r"\(cid:\d+\)")

def needs_ocr(txt: str) -> tuple[bool, str]:
    if len(txt.strip()) < N_MIN:
        return True, "empty"
    junk = len(CID_RE.findall(txt))
    total_tokens = max(len(txt.split()), 1)
    if junk / total_tokens > JUNK_RATIO:
        return True, "garbled"
    return False, "ok"

def parse_pdf(pdf_path, out_dir, stem, doc_id, ocr_log):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    wf = open(out / f"{stem}.words.jsonl", "w", encoding="utf-8")
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            n = page.page_number
            txt = page.extract_text(x_tolerance=1.5,
                                     y_tolerance=3) or ""
            trigger, reason = needs_ocr(txt)
            if trigger:
                ocr_log.write(f"{doc_id},{n},trigger,{reason}\n")
                txt, ocr_words = ocr_page(page, doc_id, ocr_log)
                for w in ocr_words:
                    rec = {"doc_id": doc_id, "page": n,
                           "text": w["text"], "bbox": w["bbox"],
                           "units": "pt", "origin": "top-left",
                           "ocr": True, "ocr_conf": w["conf"]}
                    wf.write(json.dumps(rec) + "\n")
            else:
                for w in page.extract_words(use_text_flow=True):
                    rec = {"doc_id": doc_id, "page": n,
                           "text": w["text"],
                           "bbox": [w["x0"], w["top"],
                                    w["x1"], w["bottom"]],
                           "units": "pt", "origin": "top-left",
                           "ocr": False}
                    wf.write(json.dumps(rec) + "\n")

            p = out / f"{stem}_p{n:04d}.txt"
            p.write_text(txt, encoding="utf-8")
    wf.close()

if __name__ == "__main__":
    Path("data/parsed").mkdir(parents=True, exist_ok=True)
    with open("data/parsed/ocr_log.csv", "w") as ocr_log:
        for pdf_path in Path("data/rendered").glob("*.pdf"):
            stem = pdf_path.stem
            parse_pdf(pdf_path, "data/parsed", stem, doc_id=stem, ocr_log=ocr_log)
            print(f"parsed: {stem}")