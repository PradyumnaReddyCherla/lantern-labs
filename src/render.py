import re
from pathlib import Path
from playwright.sync_api import sync_playwright

RAW, OUT = Path("data/raw"), Path("data/rendered")
PER = re.compile(r"CONFORMED PERIOD OF REPORT:\s*(\d{8})")

def details_file(d):
    for n in ("primary-document.html", "filing-details.html"):
        if (d / n).exists():
            return d / n
    raise FileNotFoundError(d)

def out_name(d):
    hdr = (d / "full-submission.txt").read_text(errors="ignore")
    m = PER.search(hdr[:5000])
    per = m.group(1)
    form = d.parts[-2].replace("-", "")
    return f"{d.parts[-3]}_{form}_{per}.pdf"

OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    for sub in RAW.rglob("full-submission.txt"):
        page = browser.new_page()
        page.goto(details_file(sub.parent).resolve().as_uri())
        page.pdf(path=str(OUT / out_name(sub.parent)),
                 format="Letter", print_background=True)
        page.close()
    browser.close()