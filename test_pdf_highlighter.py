
from pathlib import Path
from pdf_processor import process_pdf
from search_engine import search_pages
from pdf_highlighter import highlight_pdf

pdf_path = input("Enter the full path of your PDF: ").strip().strip('"')
query = input("Enter a word or phrase to highlight: ").strip()

source = Path(pdf_path)

if not source.is_file():
    print("ERROR: PDF file not found.")
else:
    pages = process_pdf(str(source))
    results = search_pages(pages, query)

    print(f"\nMatches found: {len(results)}")

    if results:
        output_path = source.with_name(
            f"{source.stem}_highlighted.pdf"
        )

        highlight_pdf(str(source), str(output_path), results)

        print(f"Highlighted PDF saved to:\n{output_path}")
        print("Open the highlighted PDF to verify the results.")
    else:
        print("No matches found. Try a different search phrase.")
