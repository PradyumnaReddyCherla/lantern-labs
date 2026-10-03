from pathlib import Path
from docling.document_converter import (
    DocumentConverter, PdfFormatOption)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, TableFormerMode)

opts = PdfPipelineOptions(do_ocr=False, do_table_structure=True)
opts.table_structure_options.mode = TableFormerMode.ACCURATE

conv = DocumentConverter(format_options={InputFormat.PDF:
    PdfFormatOption(pipeline_options=opts)})

if __name__ == "__main__":
    stem = "AAPL_10K_20250927"
    out = Path("data/docling")
    out.mkdir(parents=True, exist_ok=True)

    print(f"Converting {stem} (first Linux run downloads Docling models, be patient)...")
    doc = conv.convert(f"data/rendered/{stem}.pdf").document

    (out / f"{stem}.md").write_text(doc.export_to_markdown(), encoding="utf-8")
    doc.save_as_json(out / f"{stem}.json")

    for i, t in enumerate(doc.tables):
        df = t.export_to_dataframe(doc=doc)
        df.to_csv(out / f"{stem}_t{i:03d}.csv", index=False)

    print(f"done: {len(doc.tables)} tables found")
