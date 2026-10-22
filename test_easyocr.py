
import easyocr
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from difflib import SequenceMatcher
import re

# --------------------------------------------------
# 1. Get the image path
# --------------------------------------------------

image_path = input(
    "Enter the full image path: "
).strip().strip('"')

source = Path(image_path)

if not source.is_file():
    print("ERROR: Image file not found.")
    raise SystemExit

try:
    # --------------------------------------------------
    # 2. Open and enhance the image
    # --------------------------------------------------

    original = Image.open(source).convert("RGB")

    print("\nOriginal image size:", original.size)

    enhanced = ImageOps.grayscale(original)
    enhanced = ImageOps.autocontrast(enhanced)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.5)

    enhanced = enhanced.resize(
        (enhanced.width * 2, enhanced.height * 2),
        Image.Resampling.LANCZOS
    )

    enhanced = enhanced.filter(
        ImageFilter.UnsharpMask(
            radius=2,
            percent=150,
            threshold=3
        )
    )

    enhanced_path = source.with_name(
        source.stem + "_enhanced.jpg"
    )

    enhanced.convert("RGB").save(
        enhanced_path,
        quality=95
    )

    print("Enhanced image saved:", enhanced_path)

    # --------------------------------------------------
    # 3. Load EasyOCR
    # --------------------------------------------------

    print("\nLoading EasyOCR model. Please wait...")

    reader = easyocr.Reader(
        ["en"],
        gpu=False
    )

    # --------------------------------------------------
    # 4. Recognize text in the original and enhanced images
    # --------------------------------------------------

    print("\nChoose the image for OCR:")
    print("1. Original photo")
    print("2. Enhanced photo")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        selected_path = str(source)
    elif choice == "2":
        selected_path = str(enhanced_path)
    else:
        print("Invalid choice. Using the enhanced photo.")
        selected_path = str(enhanced_path)

    print("\nRecognizing handwriting...")

    results = reader.readtext(
        selected_path,
        detail=0,
        paragraph=False
    )

    print("\n========== RECOGNIZED TEXT ==========\n")

    for line in results:
        print(line)

    # --------------------------------------------------
    # 5. Convert OCR output into searchable words
    # --------------------------------------------------

    recognized_words = []

    for line in results:
        for word in line.split():
            cleaned_word = re.sub(
                r"^[^\w]+|[^\w]+$",
                "",
                word.casefold()
            )

            if cleaned_word:
                recognized_words.append(cleaned_word)

    print("\nTotal detected text regions:", len(results))
    print("Total recognized words:", len(recognized_words))

    # --------------------------------------------------
    # 6. Ask for ANY search word
    # --------------------------------------------------

    while True:
        search_query = input(
            "\nEnter any word to search for "
            "(or type 'exit' to quit): "
        ).strip().casefold()

        if search_query == "exit":
            print("Search finished.")
            break

        if not search_query:
            print("Please enter a search word.")
            continue

        # Support searching for multiple words as well
        query_words = [
            re.sub(r"^[^\w]+|[^\w]+$", "", word)
            for word in search_query.split()
        ]

        query_words = [word for word in query_words if word]

        if not query_words:
            print("Please enter a valid search term.")
            continue

        # --------------------------------------------------
        # 7. Exact matching and approximate OCR matching
        # --------------------------------------------------

        exact_found = False
        approximate_matches = {}

        for i in range(len(recognized_words)):
            # Check consecutive words for a multiword query
            end = i + len(query_words)

            if end <= len(recognized_words):
                phrase = recognized_words[i:end]

                if phrase == query_words:
                    exact_found = True

            # Fuzzy matching is applied to individual words
            if len(query_words) == 1:
                word = recognized_words[i]

                similarity = SequenceMatcher(
                    None,
                    query_words[0],
                    word
                ).ratio()

                if word == query_words[0]:
                    approximate_matches[word] = 1.0

                elif similarity >= 0.55:
                    approximate_matches[word] = max(
                        approximate_matches.get(word, 0),
                        similarity
                    )

        # --------------------------------------------------
        # 8. Display results
        # --------------------------------------------------

        print(f"\n========== RESULTS FOR '{search_query}' ==========")

        if exact_found:
            print("Exact match found in OCR text.")

        if approximate_matches:
            sorted_matches = sorted(
                approximate_matches.items(),
                key=lambda item: item[1],
                reverse=True
            )

            print("\nMatching or similar recognized words:")

            for word, score in sorted_matches:
                if word == search_query:
                    print(f"Exact word: {word}")
                else:
                    print(
                        f"Possible match: {word} "
                        f"({score * 100:.1f}% similarity)"
                    )

        elif not exact_found:
            print("No exact or sufficiently similar word found.")

        if not exact_found and approximate_matches:
            print(
                "\nNote: These are possible OCR matches, "
                "not confirmed readings of the handwriting."
            )

except Exception as error:
    print("\nERROR:", error)
