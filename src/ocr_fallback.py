import pytesseract
from pytesseract import Output


DPI = 300
CFG = "--oem 1 --psm 6"  # LSTM engine; one block

def ocr_page(page, doc_id, log):
    img = page.to_image(resolution=DPI).original  # PIL image
    text = pytesseract.image_to_string(img, config=CFG)
    d = pytesseract.image_to_data(
        img, config=CFG, output_type=Output.DICT)
    k = 72 / DPI  # pixels -> points
    words = []
    for i, t in enumerate(d["text"]):
        c = float(d["conf"][i])
        if not t.strip() or c < 0:
            continue
        x, y = d["left"][i], d["top"][i]
        w, h = d["width"][i], d["height"][i]
        words.append({"text": t, "conf": c,
                       "bbox": [x*k, y*k, (x+w)*k, (y+h)*k]})
    mean = sum(w["conf"] for w in words) / max(len(words), 1)
    log.write(f"{doc_id},{page.page_number},ocr,{mean:.1f}\n")
    return text, words