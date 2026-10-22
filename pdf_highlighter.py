
import pymupdf


def highlight_pdf(input_path, output_path, search_results):
    """
    Highlight matching words in the original PDF.

    Direct-extraction coordinates can be used directly.
    OCR coordinates are also converted to PDF coordinates
    by pdf_processor.py.
    """
    document = pymupdf.open(input_path)

    try:
        for result in search_results:
            page_index = result["page_number"] - 1

            if not (0 <= page_index < len(document)):
                continue

            page = document[page_index]

            for position in result["positions"]:
                rect = pymupdf.Rect(
                    position["x0"],
                    position["y0"],
                    position["x1"],
                    position["y1"],
                )

                # Add a small margin so the highlight covers the word.
                rect = rect + (-0.5, -0.5, 0.5, 0.5)

                annotation = page.add_highlight_annot(rect)
                annotation.update()

        document.save(output_path, garbage=4, deflate=True)

    finally:
        document.close()
