
import pymupdf
import pytesseract
from PIL import Image
from io import BytesIO

# Configure Tesseract OCR for Windows
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def process_pdf(pdf_path):
    """
    Process a PDF page by page.

    Typed pages use direct PDF text extraction.
    Scanned pages use Tesseract OCR.

    Returns text and word positions for every page.
    """
    document = pymupdf.open(pdf_path)
    results = []

    try:
        for page_number, page in enumerate(document):
            # First, try extracting digitally stored text.
            words = page.get_text("words")

            # Use OCR if the page has too little extractable text.
            if len(words) >= 5:
                method = "direct"
                extracted_text = page.get_text()
                word_positions = []

                for word in words:
                    word_positions.append({
                        "text": word[4],
                        "x0": word[0],
                        "y0": word[1],
                        "x1": word[2],
                        "y1": word[3],
                    })

            else:
                method = "ocr"

                # Render the page at 2x resolution for OCR.
                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2),
                    alpha=False
                )

                image = Image.open(
                    BytesIO(pix.tobytes("png"))
                )

                # OCR returns word positions in image pixels.
                ocr_data = pytesseract.image_to_data(
                    image,
                    output_type=pytesseract.Output.DICT
                )

                word_positions = []
                text_parts = []

                # Convert OCR pixel coordinates back to PDF coordinates.
                scale_x = page.rect.width / image.width
                scale_y = page.rect.height / image.height

                for i, raw_word in enumerate(ocr_data["text"]):
                    word_text = raw_word.strip()

                    if not word_text:
                        continue

                    try:
                        confidence = float(
                            ocr_data["conf"][i]
                        )
                    except (ValueError, TypeError):
                        confidence = -1

                    if confidence < 0:
                        continue

                    x0 = ocr_data["left"][i] * scale_x
                    y0 = ocr_data["top"][i] * scale_y
                    x1 = (
                        ocr_data["left"][i]
                        + ocr_data["width"][i]
                    ) * scale_x
                    y1 = (
                        ocr_data["top"][i]
                        + ocr_data["height"][i]
                    ) * scale_y

                    word_positions.append({
                        "text": word_text,
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "confidence": confidence,
                    })

                    text_parts.append(word_text)

                extracted_text = " ".join(text_parts)

            results.append({
                "page_number": page_number + 1,
                "method": method,
                "text": extracted_text,
                "words": word_positions,
            })

    finally:
        document.close()

    return results
