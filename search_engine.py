
import re


def normalize_word(text):
    """Normalize a word for case-insensitive matching."""
    return re.sub(r"^[^\w]+|[^\w]+$", "", text.casefold())


def search_pages(pages, query):
    """
    Search processed PDF pages and return matching word positions.

    Each result includes the page number, extraction method,
    matched words, and their PDF coordinates.
    """
    query_words = [
        normalize_word(word)
        for word in query.split()
    ]
    query_words = [word for word in query_words if word]

    if not query_words:
        return []

    results = []

    for page in pages:
        words = page.get("words", [])
        normalized_words = [
            normalize_word(word["text"])
            for word in words
        ]

        for start in range(len(normalized_words)):
            end = start + len(query_words)

            if normalized_words[start:end] == query_words:
                matched_words = words[start:end]

                results.append({
                    "page_number": page["page_number"],
                    "method": page["method"],
                    "matched_text": " ".join(
                        word["text"] for word in matched_words
                    ),
                    "positions": [
                        {
                            "x0": word["x0"],
                            "y0": word["y0"],
                            "x1": word["x1"],
                            "y1": word["y1"],
                        }
                        for word in matched_words
                    ],
                })

    return results
