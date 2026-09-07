"""
PDF Service
===========
Handles PDF ingestion and page-by-page text extraction using PyMuPDF (fitz).
Extracts raw text while preserving page number boundaries to enable precise
evidence grounding for downstream fact extraction.
"""

import io
try:
    import pymupdf as fitz
except ImportError:
    import fitz  # Fallback for older versions
from typing import List, Dict, Any, Union, BinaryIO


class PDFService:
    """Service for handling PDF text extraction."""

    @staticmethod
    def extract_text_page_by_page(
        pdf_source: Union[str, bytes, BinaryIO],
        filename: str = "document.pdf"
    ) -> Dict[str, Any]:
        """
        Extracts text from each page of a PDF document.

        Args:
            pdf_source: File path (str), raw file bytes (bytes), or file-like object (BinaryIO).
            filename: Name of the file for logging and metadata.

        Returns:
            Dict containing:
                - filename: str
                - total_pages: int
                - pages: List[Dict[str, Any]] with keys:
                    - page_number: int (1-based index)
                    - text: str (extracted text)
                    - char_count: int
        """
        doc = None
        try:
            if isinstance(pdf_source, str):
                doc = fitz.open(pdf_source)
            elif isinstance(pdf_source, bytes):
                doc = fitz.open(stream=pdf_source, filetype="pdf")
            elif hasattr(pdf_source, "read"):
                # Handle file-like objects such as Streamlit UploadedFile
                content = pdf_source.read()
                if hasattr(pdf_source, "seek"):
                    pdf_source.seek(0)
                doc = fitz.open(stream=content, filetype="pdf")
            else:
                raise ValueError(f"Unsupported PDF source type: {type(pdf_source)}")

            total_pages = len(doc)
            extracted_pages: List[Dict[str, Any]] = []

            for page_index in range(total_pages):
                page = doc.load_page(page_index)
                page_text = page.get_text("text")

                # Clean basic whitespace artifacts while preserving line breaks
                cleaned_text = page_text.strip()

                extracted_pages.append({
                    "page_number": page_index + 1,  # 1-indexed for human readability and citing
                    "text": cleaned_text,
                    "char_count": len(cleaned_text),
                })

            return {
                "filename": filename,
                "total_pages": total_pages,
                "pages": extracted_pages,
            }

        except Exception as exc:
            raise RuntimeError(f"Failed to extract text from PDF '{filename}': {str(exc)}") from exc

        finally:
            if doc is not None:
                doc.close()
