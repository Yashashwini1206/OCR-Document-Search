
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
from pytesseract import Output
import io

# Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def process_pdf(pdf_path):
    pdf_path = Path(pdf_path)

    if not pdf_path.is_file():
        print("ERROR: PDF file not found.")
        return

    doc = pymupdf.open(pdf_path)

    print(f"\nFile: {pdf_path.name}")
    print(f"Total pages: {len(doc)}")

    for page_number, page in enumerate(doc, start=1):
        print(f"\n--- PAGE {page_number} ---")

        # Try extracting digital text first
        words = page.get_text("words")

        if len(words) >= 5:
            print("Method: Direct PDF text extraction")

            for word in words[:15]:
                x0, y0, x1, y1, text = word[:5]
                print(
                    f"{text} | "
                    f"position=({x0:.1f}, {y0:.1f}) | "
                    f"size=({x1-x0:.1f}, {y1-y0:.1f})"
                )

        else:
            print("Method: OCR")

            # Render the PDF page to an image
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                alpha=False
            )

            image = Image.open(
                io.BytesIO(pix.tobytes("png"))
            )

            data = pytesseract.image_to_data(
                image,
                lang="eng",
                output_type=Output.DICT
            )

            count = 0

            for i, text in enumerate(data["text"]):
                text = text.strip()

                if text and int(data["conf"][i]) >= 0:
                    print(
                        f"{text} | "
                        f"confidence={data['conf'][i]} | "
                        f"image_position=("
                        f"{data['left'][i]}, "
                        f"{data['top'][i]})"
                    )
                    count += 1

                    if count >= 15:
                        break

            print(f"Sample OCR words shown: {count}")

    doc.close()


pdf_path = input("Enter the full path of a PDF: ").strip().strip('"')
process_pdf(pdf_path)
