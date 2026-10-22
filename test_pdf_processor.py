
from pathlib import Path
from pdf_processor import process_pdf

pdf_path = input("Enter the full path of your PDF: ").strip().strip('"')

if not Path(pdf_path).is_file():
    print("ERROR: PDF file not found. Check the path.")
else:
    try:
        pages = process_pdf(pdf_path)

        print(f"\nTotal pages processed: {len(pages)}")

        for page in pages:
            print(f"\n--- PAGE {page['page_number']} ---")
            print(f"Method: {page['method']}")
            print(f"Detected words: {len(page['words'])}")
            print("Extracted text preview:")
            print(page["text"][:700])

            if page["words"]:
                print("\nFirst 5 word positions:")
                for word in page["words"][:5]:
                    print(word)

    except Exception as error:
        print(f"ERROR: {error}")
