
import re
from difflib import SequenceMatcher


def normalize_word(text):
    """Lowercase and remove punctuation for matching."""
    return re.sub(r"[^a-z0-9]", "", text.casefold())


def similarity(a, b):
    """Compare normalized OCR text with the search term."""
    return SequenceMatcher(None, a, b).ratio()


def search_pages(pages, query):
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
        normalized = [
            normalize_word(word.get("text", ""))
            for word in words
        ]

        for start, candidate in enumerate(normalized):
            if not candidate:
                continue

            # Exact single-word match after normalization.
            if len(query_words) == 1 and candidate == query_words[0]:
                matched = words[start:start + 1]
                results.append({
                    "page_number": page["page_number"],
                    "method": page["method"],
                    "matched_text": matched[0]["text"],
                    "positions": [
                        {
                            "x0": w["x0"],
                            "y0": w["y0"],
                            "x1": w["x1"],
                            "y1": w["y1"],
                        }
                        for w in matched
                    ],
                    "match_type": "exact",
                    "confidence": matched[0].get("confidence"),
                })
                continue

            # Fuzzy fallback is for single-word OCR variations only.
            if len(query_words) != 1:
                continue

            target = query_words[0]

            # Short strings are too ambiguous for fuzzy matching.
            if len(target) < 4 or len(candidate) < 3:
                continue

            # Permit a limited length difference for OCR omissions.
            if abs(len(target) - len(candidate)) > 2:
                continue

            score = similarity(target, candidate)

            # Conservative threshold; results remain unverified.
            if score >= 0.70:
                w = words[start]
                results.append({
                    "page_number": page["page_number"],
                    "method": page["method"],
                    "matched_text": w["text"],
                    "positions": [{
                        "x0": w["x0"],
                        "y0": w["y0"],
                        "x1": w["x1"],
                        "y1": w["y1"],
                    }],
                    "match_type": "possible",
                    "confidence": score,
                })

    # Prefer exact matches and avoid repeated identical boxes.
    results.sort(
        key=lambda result: (
            result["match_type"] != "exact",
            result["page_number"],
        )
    )

    unique_results = []
    seen = set()

    for result in results:
        position_key = tuple(
            (
                round(p["x0"], 1),
                round(p["y0"], 1),
                round(p["x1"], 1),
                round(p["y1"], 1),
            )
            for p in result["positions"]
        )

        key = (
            result["page_number"],
            result["matched_text"].casefold(),
            position_key,
        )

        if key not in seen:
            seen.add(key)
            unique_results.append(result)

    return unique_results
