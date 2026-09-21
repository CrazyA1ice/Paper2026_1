from pathlib import Path
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "word_output" / "2026.09.21v18.docx"
OUT = ROOT / "word_output" / "v18_text_dump.txt"

doc = Document(SRC)
lines = []
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if t:
        lines.append(f"[P{i:04d}] {t}")
OUT.write_text("\n".join(lines), encoding="utf-8")
print(OUT)
