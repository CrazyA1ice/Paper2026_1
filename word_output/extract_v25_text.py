from pathlib import Path
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "word_output" / "2026.09.23v25.docx"
out = ROOT / "word_output" / "v25_text_dump.txt"

doc = Document(src)
with out.open("w", encoding="utf-8") as f:
    for i, p in enumerate(doc.paragraphs):
        text = p.text.replace("\n"," ").strip()
        if text:
            f.write(f"[{i:04d}] {text}\n")
print(out)
