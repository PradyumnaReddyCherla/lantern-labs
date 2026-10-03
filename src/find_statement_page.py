import pdfplumber

def find_page(pdf_path: str, heading: str) -> int | None:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if heading.upper() in text.upper():
                return page.page_number
    return None

if __name__ == "__main__":
    pdf = "data/rendered/AAPL_10K_20250927.pdf"
    for heading in ["CONSOLIDATED STATEMENTS OF OPERATIONS",
                    "CONSOLIDATED BALANCE SHEETS",
                    "CONSOLIDATED STATEMENTS OF CASH FLOWS"]:
        p = find_page(pdf, heading)
        print(f"{heading}: page {p}")