import re
from pathlib import Path

KEEP = {".htm", ".html", ".xml", ".xsd"}  # no images

def unpack(sub: Path) -> Path:
    out = sub.parent / "unpacked"
    out.mkdir(exist_ok=True)
    raw = sub.read_text(errors="ignore")
    for doc in re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>", raw, re.S):
        name = re.search(r"<FILENAME>([^\n<]+)", doc)
        body = re.search(r"<TEXT>\n?(.*?)</TEXT>", doc, re.S)
        if not (name and body):
            continue
        fn = name.group(1).strip()
        if Path(fn).suffix.lower() not in KEEP:
            continue
        text = body.group(1)
        x = re.search(r"<(XBRL|XML)>\n?(.*?)</\1>", text, re.S)
        (out / fn).write_text(x.group(2) if x else text)
    return out

for sub in Path("data/raw").rglob("full-submission.txt"):
    unpack(sub)
    print(f"unpacked: {sub.parent}")