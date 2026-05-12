"""
utils/pdf_reader.py
-------------------
Handles PDF text extraction using pdfplumber (primary) with PyPDF2 as fallback.
Beginner-friendly: every function is heavily commented.
"""

import pdfplumber          # Best-in-class PDF text extractor
import PyPDF2              # Fallback extractor
import io                  # Needed to work with in-memory file bytes
import streamlit as st     # For showing error messages inside the app


def extract_text_pdfplumber(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF using pdfplumber.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        A single string containing all extracted text, or "" on failure.
    """
    text_parts = []  # We'll collect text page-by-page

    try:
        # Open the PDF from memory (no need to save it to disk)
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()  # pdfplumber magic

                if page_text:  # Some pages (e.g. image-only) return None
                    text_parts.append(page_text)
                else:
                    # Warn but keep going — don't crash on one blank page
                    st.warning(f"⚠️ Page {page_number} had no extractable text "
                               f"(it may be a scanned image).")

        return "\n".join(text_parts)

    except Exception as e:
        # Return empty string so the caller can decide what to do
        st.error(f"pdfplumber extraction failed: {e}")
        return ""


def extract_text_pypdf2(pdf_bytes: bytes) -> str:
    """
    Fallback: extract text using PyPDF2.

    PyPDF2 is less accurate than pdfplumber but handles some edge-case PDFs better.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Extracted text string, or "" on failure.
    """
    text_parts = []

    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        return "\n".join(text_parts)

    except Exception as e:
        st.error(f"PyPDF2 extraction failed: {e}")
        return ""


def extract_resume_text(pdf_bytes: bytes) -> str:
    """
    Main entry point: tries pdfplumber first, falls back to PyPDF2.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Cleaned resume text string. Raises ValueError if both methods fail.
    """
    # --- Attempt 1: pdfplumber (preferred) ---
    text = extract_text_pdfplumber(pdf_bytes)

    # --- Attempt 2: PyPDF2 fallback ---
    if not text.strip():
        st.info("Trying fallback PDF reader…")
        text = extract_text_pypdf2(pdf_bytes)

    # --- Give up gracefully ---
    if not text.strip():
        raise ValueError(
            "Could not extract any text from this PDF. "
            "It may be a scanned image. Please upload a text-based PDF."
        )

    # Basic cleanup: remove excessive blank lines
    cleaned = "\n".join(
        line for line in text.splitlines() if line.strip()
    )

    return cleaned


def get_pdf_metadata(pdf_bytes: bytes) -> dict:
    """
    Return basic metadata about the uploaded PDF.

    Useful for displaying a quick summary to the user before analysis.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Dict with keys: page_count, word_count, char_count.
    """
    metadata = {"page_count": 0, "word_count": 0, "char_count": 0}

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            metadata["page_count"] = len(pdf.pages)

        text = extract_resume_text(pdf_bytes)
        metadata["word_count"] = len(text.split())
        metadata["char_count"] = len(text)

    except Exception:
        pass  # Metadata is nice-to-have; don't crash for it

    return metadata
