import json
import pandas as pd
from pathlib import Path

records = [json.loads(l) for l in Path("data/export/AAPL_10K_20250927.jsonl").read_text(encoding="utf-8").splitlines()]

# --- Markdown ---
def table_md(t):
    df = pd.DataFrame(t["rows"], columns=t["columns"])
    return df.to_markdown(index=False)

md_lines = []
current_section = None
for r in records:
    if r.get("section") != current_section:
        current_section = r.get("section")
        md_lines.append(f"\n## {current_section or 'Untitled'}\n")
    src = f"<!-- {r['doc_id']} p{r['page']} {r['block_id']} -->"
    if r["block_type"] == "Table" and r["table"]:
        md_lines += [src, table_md(r["table"])]
    elif r.get("text"):
        md_lines += [src, r["text"]]

md_out = "\n\n".join(md_lines)
Path("data/export/AAPL_10K_20250927.md").write_text(md_out, encoding="utf-8")

# --- TXT: flattened, no structure, no provenance ---
txt_out = "\n\n".join(r.get("text") or str(r.get("table")) for r in records)
Path("data/export/AAPL_10K_20250927.txt").write_text(txt_out, encoding="utf-8")

# --- Compare ---
print(f"{'format':<12}{'bytes':>10}{'~tokens':>10}")
for fname in ["AAPL_10K_20250927.jsonl", "AAPL_10K_20250927.md", "AAPL_10K_20250927.txt"]:
    p = Path("data/export") / fname
    size = p.stat().st_size
    approx_tokens = size / 4  # deck's own chars/4 heuristic
    print(f"{fname:<28}{size:>8}{approx_tokens:>10.0f}")