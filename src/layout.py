import json
import numpy as np
import pdfplumber
import torch
import layoutparser as lp
from pathlib import Path
Path("data/layout").mkdir(parents=True, exist_ok=True)
from huggingface_hub import hf_hub_download

# Fix 1: PyTorch 2.6 weights_only default blocks old checkpoints
_orig_load = torch.load
torch.load = lambda *a, **k: _orig_load(*a, **{**k, "weights_only": False})

DPI, K = 150, 72 / 150
LABEL_MAP = {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}

def label_of(b):
    """b.type may be an int class id or already a string label."""
    t = b.type
    return LABEL_MAP.get(t, str(t)) if isinstance(t, int) else str(t)

print("Loading PubLayNet model from Hugging Face weights...")
weights = hf_hub_download(
    repo_id="layoutparser/efficientdet",
    filename="PubLayNet/tf_efficientdet_d0/publaynet-tf_efficientdet_d0.pth.tar")
model = lp.models.effdet.layoutmodel.EfficientDetLayoutModel(
    "tf_efficientdet_d0", model_path=weights, label_map=LABEL_MAP)
print("Model loaded.\n")

def layout_pdf(pdf_path, doc_id, out_jsonl, pages=None):
    with pdfplumber.open(pdf_path) as pdf, \
         open(out_jsonl, "w", encoding="utf-8") as f:
        page_list = pdf.pages if pages is None else [pdf.pages[p-1] for p in pages]
        for page in page_list:
            img = page.to_image(resolution=DPI).original
            layout = model.detect(np.array(img))
            labels = []
            for b in layout:
                x1, y1, x2, y2 = b.coordinates
                lbl = label_of(b)
                labels.append(lbl)
                rec = {"doc_id": doc_id,
                       "page": page.page_number,
                       "block_type": lbl,
                       "score": round(float(b.score), 3),
                       "bbox": [x1*K, y1*K, x2*K, y2*K],
                       "units": "pt", "origin": "top-left",
                       "model": "efficientdet/PubLayNet"}
                f.write(json.dumps(rec) + "\n")
            print(f"  page {page.page_number}: {len(layout)} blocks "
                  f"({', '.join(labels)})")

if __name__ == "__main__":
    pdf_path = "data/rendered/AAPL_10K_20250927.pdf"
    doc_id = "AAPL_10K_20250927"
    test_pages = [1, 2, 32]
    print(f"Running layout detection on pages {test_pages} of {doc_id}...")
    layout_pdf(pdf_path, doc_id, "data/layout/AAPL_10K_20250927.layout.jsonl",
               pages=test_pages)
    print("\ndone -> data/layout/AAPL_10K_20250927.layout.jsonl")
