
import streamlit as st
import pymupdf
import pytesseract

from pathlib import Path
from tempfile import NamedTemporaryFile
from PIL import Image, ImageDraw


from pdf_processor import process_pdf
from search_engine import search_pages


# =========================================================
# CONFIGURATION
# =========================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

st.set_page_config(
    page_title="OCR Document Search",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# PROFESSIONAL LIGHT THEME
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F7FB;
        color: #1E293B;
    }

    [data-testid="stSidebar"] {
        background-color: #102A43;
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC;
    }

    [data-testid="stSidebar"] input {
        color: #1E293B !important;
        background-color: #FFFFFF !important;
    }

    .main-header {
        font-size: 30px;
        font-weight: 750;
        color: #102A43;
        margin-bottom: 4px;
    }

    .sub-header {
        color: #64748B;
        font-size: 15px;
        margin-bottom: 22px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #102A43;
        margin-top: 12px;
        margin-bottom: 10px;
    }

    .stat-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        min-height: 108px;
    }

    .stat-label {
        font-size: 13px;
        color: #64748B;
        margin-bottom: 8px;
    }

    .stat-value {
        font-size: 28px;
        font-weight: 750;
        color: #102A43;
    }

    .info-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
    }

    div.stButton > button[kind="primary"] {
        background-color: #1765A3;
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        min-height: 44px;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: #124D7C;
        color: white;
    }

    hr {
        border-color: #E2E8F0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# PROCESS A PDF OR IMAGE
# =========================================================

def process_uploaded_file(file_path):
    """Extract words and their positions from a PDF or image."""

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        # Reuse the existing PDF text extraction and OCR.
        return process_pdf(file_path)

    with Image.open(file_path) as original:
        image = original.convert("RGB")

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
    )

    words = []
    text_parts = []

    for i, raw_text in enumerate(data["text"]):
        word = raw_text.strip()

        if not word:
            continue

        try:
            confidence = float(data["conf"][i])
        except (ValueError, TypeError):
            confidence = -1

        if confidence < 0:
            continue

        x0 = data["left"][i]
        y0 = data["top"][i]
        x1 = x0 + data["width"][i]
        y1 = y0 + data["height"][i]

        words.append({
            "text": word,
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
            "confidence": confidence,
        })

        text_parts.append(word)

    return [{
        "page_number": 1,
        "method": "ocr",
        "text": " ".join(text_parts),
        "words": words,
    }]


# =========================================================
# HIGHLIGHT A PDF PAGE FOR THE WEBPAGE PREVIEW
# =========================================================

def render_highlighted_pdf_page(pdf_path, page_number, page_results):
    """Render a PDF page and overlay highlights without changing it."""

    with pymupdf.open(pdf_path) as document:
        page = document[page_number - 1]

        zoom = 1.6
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(zoom, zoom),
            alpha=False,
        )

        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples,
        )

    draw = ImageDraw.Draw(image, "RGBA")

    for result in page_results:
        for position in result.get("positions", []):
            x0 = int(position["x0"] * zoom)
            y0 = int(position["y0"] * zoom)
            x1 = int(position["x1"] * zoom)
            y1 = int(position["y1"] * zoom)

            draw.rectangle(
                (x0, y0, x1, y1),
                fill=(255, 230, 0, 100),
                outline=(235, 130, 0, 255),
                width=3,
            )

    return image


# =========================================================
# HIGHLIGHT AN IMAGE FOR THE WEBPAGE PREVIEW
# =========================================================

def render_highlighted_image(image_path, results):
    """Return a highlighted image preview."""

    with Image.open(image_path) as original:
        image = original.convert("RGB")

    draw = ImageDraw.Draw(image, "RGBA")

    for result in results:
        for position in result.get("positions", []):
            draw.rectangle(
                (
                    position["x0"],
                    position["y0"],
                    position["x1"],
                    position["y1"],
                ),
                fill=(255, 230, 0, 100),
                outline=(235, 130, 0, 255),
                width=3,
            )

    return image


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("# 🔎 DocuSearch")
    st.caption("OFFICE DOCUMENT MANAGEMENT")
    st.divider()

    st.markdown("### Search documents")

    uploaded_files = st.file_uploader(
        "Choose multiple documents",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="You can select several PDFs and images together.",
        key="multi_document_uploader",
    )

    query = st.text_input(
        "Search term",
        placeholder="e.g. Machine Learning",
        key="multi_document_query",
    )

    search_clicked = st.button(
        "🔍  Search all documents",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    st.caption("Supported: PDF, JPG, JPEG, PNG")
    st.caption("PDF processing: PyMuPDF + OCR")
    st.caption("Image OCR: Tesseract")


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    '<div class="main-header">Document Search Dashboard</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-header">'
    'Search multiple documents at once and inspect highlighted matches.'
    '</div>',
    unsafe_allow_html=True,
)

st.info(
    "Select multiple documents in the sidebar, enter one search term, "
    "and click Search all documents."
)


# =========================================================
# PROCESS ALL UPLOADED FILES
# =========================================================

if search_clicked:
    if not uploaded_files:
        st.warning("Please upload at least one document.")

    elif not query.strip():
        st.warning("Please enter a word or phrase to search.")

    else:
        documents = []
        errors = []

        with st.spinner(
            f"Searching {len(uploaded_files)} document(s)..."
        ):
            progress = st.progress(0)

            for index, uploaded_file in enumerate(uploaded_files):
                input_path = None

                try:
                    extension = Path(uploaded_file.name).suffix.lower()

                    with NamedTemporaryFile(
                        suffix=extension,
                        delete=False,
                    ) as temp:
                        temp.write(uploaded_file.getvalue())
                        input_path = Path(temp.name)

                    pages = process_uploaded_file(str(input_path))
                    results = search_pages(pages, query.strip())

                    documents.append({
                        "name": uploaded_file.name,
                        "path": str(input_path),
                        "extension": extension,
                        "pages": pages,
                        "results": results,
                    })

                except Exception as error:
                    errors.append(
                        f"{uploaded_file.name}: {error}"
                    )

                    if input_path and input_path.exists():
                        try:
                            input_path.unlink()
                        except OSError:
                            pass

                progress.progress(
                    (index + 1) / len(uploaded_files)
                )

        # Remove temporary copies from the previous successful search.
        old_documents = st.session_state.get(
            "multi_search_documents", []
        )

        for old_doc in old_documents:
            old_path = Path(old_doc["path"])

            try:
                if old_path.exists():
                    old_path.unlink()
            except OSError:
                pass

        st.session_state["multi_search_documents"] = documents
        st.session_state["multi_search_query"] = query.strip()
        st.session_state["multi_search_errors"] = errors
        st.session_state["multi_search_completed"] = True


# =========================================================
# DISPLAY COMBINED RESULTS
# =========================================================

if st.session_state.get("multi_search_completed", False):

    documents = st.session_state.get(
        "multi_search_documents", []
    )
    query_used = st.session_state.get(
        "multi_search_query", ""
    )
    errors = st.session_state.get(
        "multi_search_errors", []
    )

    total_pages = sum(
        len(doc["pages"]) for doc in documents
    )

    total_matches = sum(
        len(doc["results"]) for doc in documents
    )

    matching_documents = sum(
        1 for doc in documents if doc["results"]
    )

    total_ocr_pages = sum(
        1
        for doc in documents
        for page in doc["pages"]
        if page.get("method") == "ocr"
    )

    st.markdown(
        '<div class="section-title">Search overview</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-label">Documents processed</div>'
            f'<div class="stat-value">{len(documents)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-label">Pages processed</div>'
            f'<div class="stat-value">{total_pages}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-label">Matches found</div>'
            f'<div class="stat-value">{total_matches}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-label">Documents with matches</div>'
            f'<div class="stat-value">{matching_documents}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown(f"**Search term:** `{query_used}`")
    st.markdown(f"**OCR-processed pages:** {total_ocr_pages}")

    if errors:
        with st.expander(
            f"Processing errors ({len(errors)})",
            expanded=True,
        ):
            for error in errors:
                st.error(error)

    st.divider()

    # -----------------------------------------------------
    # RESULTS BY DOCUMENT
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">Results by document</div>',
        unsafe_allow_html=True,
    )

    if not documents:
        st.error(
            "None of the uploaded documents could be processed. "
            "Check the errors above and try again."
        )

    elif total_matches == 0:
        st.warning(
            "No exact matches were found in the processed documents. "
            "Try another spelling or search term. Handwriting may be "
            "misrecognised by OCR."
        )

    for doc in documents:
        doc_results = doc["results"]

        with st.expander(
            f"📄 {doc['name']} — {len(doc_results)} match(es)",
            expanded=bool(doc_results),
        ):
            if not doc_results:
                st.info("No matches found in this document.")
                continue

            for match_index, result in enumerate(
                doc_results, start=1
            ):
                st.markdown(
                    f"**Match {match_index} — "
                    f"Page {result['page_number']}**"
                )
                st.write(result["matched_text"])

            st.divider()
            st.markdown("**Highlighted document preview**")

            results_by_page = {}

            for result in doc_results:
                page_number = result["page_number"]

                results_by_page.setdefault(
                    page_number, []
                ).append(result)

            for page_number, page_results in sorted(
                results_by_page.items()
            ):
                st.markdown(f"**Page {page_number}**")

                try:
                    if doc["extension"] == ".pdf":
                        preview = render_highlighted_pdf_page(
                            doc["path"],
                            page_number,
                            page_results,
                        )
                    else:
                        preview = render_highlighted_image(
                            doc["path"],
                            page_results,
                        )

                    st.image(
                        preview,
                        caption=(
                            f"{doc['name']} — Page {page_number}"
                        ),
                        use_container_width=True,
                    )

                except Exception as error:
                    st.error(
                        f"Could not preview page {page_number}: {error}"
                    )

    st.caption(
        "Highlights are displayed on previews only. "
        "The original uploaded documents are not modified."
    )


# =========================================================
# EMPTY STATE
# =========================================================

else:
    st.markdown(
        '<div class="info-card">'
        '<strong>Ready to search</strong><br>'
        '<span style="color:#64748B;">'
        'Your combined results and highlighted document previews '
        'will appear here.'
        '</span></div>',
        unsafe_allow_html=True,
    )


st.divider()

st.caption(
    "DocuSearch | Local document processing | "
    "Multiple-document search"
)
