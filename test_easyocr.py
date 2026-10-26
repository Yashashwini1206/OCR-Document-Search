import easyocr
import pymupdf
import numpy as np
from PIL import Image

pdf_path = input("Enter the full PDF path: ").strip().strip('"')

reader = easyocr.Reader(["en"], gpu=False)

with pymupdf.open(pdf_path) as pdf:
    for page_number, page in enumerate(pdf, start=1):
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(3, 3),
            alpha=False
        )

        image = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        import numpy as np

        results = reader.readtext(
            np.array(image),
            detail=1,
            paragraph=False
        )

        print(f"\n--- Page {page_number} ---")
        print("EasyOCR recognized:")

        for box, text, confidence in results:
            print(f"{text} | confidence={confidence:.2f}")
