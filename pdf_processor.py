
import pymupdf
import pytesseract
import easyocr
import numpy as np
from PIL import Image
from io import BytesIO

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

_easyocr_reader = None


def get_easyocr_reader():
    """Initialize EasyOCR only when a scanned page needs it."""
    global _easyocr_reader

    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(["en"], gpu=False)

    return _easyocr_reader


def boxes_overlap(a, b):
    """Return the intersection-over-union of two rectangles."""
    x0 = max(a["x0"], b["x0"])
    y0 = max(a["y0"], b["y0"])
    x1 = min(a["x1"], b["x1"])
    y1 = min(a["y1"], b["y1"])

    intersection = max(0, x1 - x0) * max(0, y1 - y0)

    area_a = max(0, a["x1"] - a["x0"]) * max(
        0, a["y1"] - a["y0"]
    )
    area_b = max(0, b["x1"] - b["x0"]) * max(
        0, b["y1"] - b["y0"]
    )

    union = area_a + area_b - intersection
    return intersection / union if union else 0


def process_pdf(pdf_path):
    """
    Extract text and word positions from every PDF page.

    Pages with selectable text use direct extraction.
    Scanned pages use Tesseract, supplemented by EasyOCR.
    Coordinates are stored in PDF points for highlighting.
    """
    results = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            native_words = page.get_text("words")

            if len(native_words) >= 5:
                word_positions = [
                    {
                        "text": word[4],
                        "x0": word[0],
                        "y0": word[1],
                        "x1": word[2],
                        "y1": word[3],
                    }
                    for word in native_words
                ]

                results.append({
                    "page_number": page_number,
                    "method": "direct",
                    "text": page.get_text("text"),
                    "words": word_positions,
                })
                continue

            # Render scanned page at high resolution.
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(3, 3),
                alpha=False,
            )
            image = Image.open(
                BytesIO(pix.tobytes("png"))
            ).convert("RGB")

            scale_x = page.rect.width / image.width
            scale_y = page.rect.height / image.height

            # First OCR pass: Tesseract.
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config="--psm 6",
                lang="eng",
            )

            word_positions = []

            for i, raw_text in enumerate(data["text"]):
                text = raw_text.strip()
                if not text:
                    continue

                try:
                    confidence = float(data["conf"][i])
                except (ValueError, TypeError):
                    continue

                if confidence < 0:
                    continue

                left = data["left"][i]
                top = data["top"][i]
                right = left + data["width"][i]
                bottom = top + data["height"][i]

                word_positions.append({
                    "text": text,
                    "x0": left * scale_x,
                    "y0": top * scale_y,
                    "x1": right * scale_x,
                    "y1": bottom * scale_y,
                    "confidence": confidence / 100.0,
                    "ocr_engine": "tesseract",
                })

            # Second OCR pass: supplement areas Tesseract missed.
            reader = get_easyocr_reader()
            detections = reader.readtext(
                np.array(image),
                detail=1,
                paragraph=False,
            )

            for polygon, detected_text, confidence in detections:
                detected_text = detected_text.strip()
                if not detected_text:
                    continue

                xs = [point[0] for point in polygon]
                ys = [point[1] for point in polygon]

                candidate = {
                    "text": detected_text,
                    "x0": min(xs) * scale_x,
                    "y0": min(ys) * scale_y,
                    "x1": max(xs) * scale_x,
                    "y1": max(ys) * scale_y,
                    "confidence": float(confidence),
                    "ocr_engine": "easyocr",
                }

                # Don't duplicate text already found by Tesseract.
                if any(
                    boxes_overlap(candidate, existing) >= 0.50
                    for existing in word_positions
                ):
                    continue

                word_positions.append(candidate)

            # Maintain reading order approximately.
            word_positions.sort(
                key=lambda word: (
                    round(word["y0"] / 8),
                    word["x0"],
                )
            )

            results.append({
                "page_number": page_number,
                "method": "ocr",
                "text": " ".join(
                    word["text"] for word in word_positions
                ),
                "words": word_positions,
            })

    return results
