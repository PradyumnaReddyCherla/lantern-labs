import camelot
import pdfplumber
from pathlib import Path
Path("data/tables").mkdir(parents=True, exist_ok=True)
from normalize import to_number, scale_from_caption

PDF = "data/rendered/AAPL_10K_20250927.pdf"
PAGE = 32  # income statement, confirmed earlier

# ----------------------------------------------------------------------
# Part 1: The bake-off — run every flavor and report shape + scores
# ----------------------------------------------------------------------
def run_camelot(flavor, **kwargs):
    try:
        tables = camelot.read_pdf(PDF, pages=str(PAGE), flavor=flavor, **kwargs)
        return [(flavor, i, t.shape,
                 t.parsing_report["accuracy"],
                 t.parsing_report["whitespace"], t)
                for i, t in enumerate(tables)]
    except Exception as e:
        print(f"  {flavor} FAILED: {e}")
        return []

print(f"{'method':<12}{'tbl':>4}{'shape':>12}{'accuracy':>10}{'whitespace':>12}")
print("-" * 50)

all_results = []
all_results += run_camelot("lattice")
all_results += run_camelot("stream", row_tol=10, edge_tol=500)
all_results += run_camelot("network")
all_results += run_camelot("hybrid")

for flavor, i, shape, acc, ws, t in all_results:
    print(f"{flavor:<12}{i:>4}{str(shape):>12}{acc:>10.2f}{ws:>12.2f}")
    t.to_csv(f"data/tables/p{PAGE}_{flavor}_{i}.csv")

# pdfplumber comparison (reported, not scored — different metric system)
with pdfplumber.open(PDF) as pdf:
    pg = pdf.pages[PAGE - 1]
    found = pg.find_tables(table_settings={
        "vertical_strategy": "text", "horizontal_strategy": "text",
        "snap_tolerance": 5, "join_tolerance": 5, "intersection_tolerance": 8,
    })
    print(f"\npdfplumber: {len(found)} table(s) found")
    for j, tbl in enumerate(found):
        rows = tbl.extract()
        empty = sum(1 for r in rows for c in r if not (c or "").strip())
        total = sum(len(r) for r in rows) or 1
        print(f"  pdfplumber table {j}: {len(rows)} rows, "
              f"{empty}/{total} empty cells ({empty/total:.0%})")

# ----------------------------------------------------------------------
# Part 2: The hybrid extractor — auto-pick the best flavor (slide 28)
# ----------------------------------------------------------------------
def ruling_count(pdf_path, page_no):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_no - 1]
        hz = [l for l in page.lines if abs(l["top"] - l["bottom"]) < 1]
        thin = [x for x in page.rects if x["height"] < 2]
        return len(hz) + len(thin)

def score(t):
    rep = t.parsing_report
    return rep["accuracy"] - 0.5 * rep["whitespace"]

def extract_best(pdf_path, page_no, thr=80, min_rows=8):
    """
    Pick the best flavor. For borderless financial statements, stream/network
    are preferred; lattice/hybrid tend to fragment them. We also reject tiny
    fragments that score high only because they captured almost nothing.
    """
    # Financial statements are overwhelmingly borderless, so try the
    # whitespace/text methods first. (The naive "count lines" heuristic
    # over-counts incidental rules and wrongly favors lattice.)
    order = ["stream", "network", "lattice", "hybrid"]
    best = None
    for flavor in order:
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(page_no), flavor=flavor)
        except Exception:
            continue
        for t in tables:
            # reject fragments: a real statement has many rows
            if t.shape[0] < min_rows:
                continue
            if best is None or score(t) > score(best[1]):
                best = (flavor, t)
        if best and score(best[1]) > thr:
            break
    return best

print("\n" + "=" * 50)
print("HYBRID EXTRACTOR (auto-select best flavor)")
print("=" * 50)
lines = ruling_count(PDF, PAGE)
print(f"Page {PAGE}: {lines} ruling lines detected")

best = extract_best(PDF, PAGE)
if best:
    flavor, t = best
    print(f"Best flavor: {flavor}  "
          f"(shape={t.shape}, score={score(t):.2f})")
    t.to_csv(f"data/tables/p{PAGE}_BEST_{flavor}.csv")
    print(f"saved -> data/tables/p{PAGE}_BEST_{flavor}.csv")

    # ----------------------------------------------------------------------
    # Part 3: Normalize the winning table's numbers (slide 29)
    # ----------------------------------------------------------------------
    print("\n--- Normalized numbers (first 10 rows) ---")
    df = t.df
    for row in df.values.tolist()[:10]:
        label = row[0]
        nums = [to_number(cell) for cell in row[1:]]
        print(f"{label[:35]:<37} {nums}")