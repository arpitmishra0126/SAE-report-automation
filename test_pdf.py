import fitz
from pathlib import Path

pdf = Path(r"data/sample_pdfs/307-9-merged-merged-compressed.pdf")

doc = fitz.open(pdf)

for i in range(4):
    page = doc.load_page(i)

    print("=" * 80)
    print("PAGE", i + 1)

    text = page.get_text("text")

    print("TEXT LENGTH:", len(text))
    print(repr(text[:500]))

    print("BLOCKS:", len(page.get_text("blocks")))
    print("WORDS:", len(page.get_text("words")))