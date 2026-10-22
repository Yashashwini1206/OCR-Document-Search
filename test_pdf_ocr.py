
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pytesseract import Output

# Location of the installed Tesseract program
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def test_pdf_ocr(pdf_path):
    pdf_path = Path(pdf_path.strip().strip('"'))

    if not pdf_path.is_file():
        print("ERROR: PDF file not found.")
        return

    if pdf_path.suffix.lower() != ".pdf":
        print("Please provide a PDF file.")
        return

    with fitz.open(pdf_path) as document:
        print(f"\nFile: {pdf_path.name}")
        print(f"Total pages: {len(document)}")

        # Test only the first 3 pages initially
        for page_number in range(min(3, len(document))):
            page = document[page_number]

            # Render the original page at higher resolution
            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False
            )

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            # Read text and word positions
            data = pytesseract.image_to_data(
                image,
                lang="eng",
                config="--psm 3",
                output_type=Output.DICT
            )

            print(f"\n--- PAGE {page_number + 1} ---")

            words_found = 0

            for i, word in enumerate(data["text"]):
                word = word.strip()

                if not word:
                    continue

                try:
                    confidence = float(data["conf"][i])
                except (ValueError, TypeError):
                    continue

                if confidence < 0:
                    continue

                x = data["left"][i]
                y = data["top"][i]
                width = data["width"][i]
                height = data["height"][i]

                print(
                    f"{word} | "
                    f"confidence={confidence:.0f} | "
                    f"position=({x}, {y}) | "
                    f"size={width}x{height}"
                )

                words_found += 1

            print(f"Words detected: {words_found}")


if __name__ == "__main__":
    pdf_path = input("Enter the full path of your PDF: ")
    test_pdf_ocr(pdf_path)
