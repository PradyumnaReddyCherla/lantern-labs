from pydantic import BaseModel, Field
from typing import Literal, Optional
import json

BlockType = Literal["Text", "Title", "List", "Table", "Figure", "Footnote"]

class Record(BaseModel):
    schema_: str = Field("lantern/1.0", alias="schema")
    doc_id: str
    company: str
    cik: str
    form: str
    fiscal_year: int
    fiscal_period: str
    page: int
    section: Optional[str] = None
    block_id: str
    block_type: BlockType
    bbox: list[float]
    units: str = "pt"
    origin: str = "top-left"
    text: Optional[str] = None
    table: Optional[dict] = None
    extractor: str
    extractor_version: str
    ocr: bool = False
    ocr_conf: Optional[float] = None
    source_path: str
    sha256: str

def write_jsonl(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(Record(**r).model_dump_json(by_alias=True) + "\n")