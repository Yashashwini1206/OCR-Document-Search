
from pdf_processor import process_pdf
from search_engine import search_pages

pdf_path = input("Enter the full path of your PDF: ").strip().strip('"')
query = input("Enter a word or phrase to search: ").strip()

pages = process_pdf(pdf_path)
results = search_pages(pages, query)

print(f"\nMatches found: {len(results)}")

for number, result in enumerate(results, start=1):
    print(f"\nMatch {number}")
    print(f"Page: {result['page_number']}")
    print(f"Method: {result['method']}")
    print(f"Matched text: {result['matched_text']}")
    print(f"Word positions: {result['positions']}")
