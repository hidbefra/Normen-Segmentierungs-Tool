"""
PDF-Handler: Handling native & scanned PDFs, OCR Layer detection, Text & BBox extraction.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFHandler:
    """Encapsulates PDF loading, OCR detection, and text/bbox extraction."""

    def __init__(self, pdf_path: str | Path):
        """
        Initialize handler with a PDF file.

        Args:
            pdf_path: Path to the PDF file.

        Raises:
            FileNotFoundError: If PDF does not exist.
            ValueError: If file is not a valid PDF.
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        try:
            self.doc = fitz.open(self.pdf_path)
        except Exception as e:
            raise ValueError(f"Invalid PDF file: {self.pdf_path}") from e

        self.page_count = len(self.doc)
        logger.info(f"Loaded PDF: {self.pdf_path.name} ({self.page_count} pages)")

    def close(self) -> None:
        """Close the PDF document."""
        if self.doc:
            self.doc.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def has_text_layer(self) -> bool:
        """
        Check if PDF has a text layer (native digital PDF or OCR layer).

        Returns:
            bool: True if text layer exists, False if scanned without OCR.
        """
        if self.page_count == 0:
            return False

        # Sample first non-empty page
        for page_num in range(min(3, self.page_count)):
            try:
                page = self.doc[page_num]
                text = page.get_text()
                if text and len(text.strip()) > 50:  # Significant text content
                    logger.debug(f"Text layer detected on page {page_num + 1}")
                    return True
            except Exception as e:
                logger.warning(f"Error checking text on page {page_num + 1}: {e}")

        logger.warning(f"No text layer detected in {self.pdf_path.name}")
        return False

    def get_page_metadata(self, page_num: int) -> Dict[str, Any]:
        """
        Get metadata for a specific page.

        Args:
            page_num: 0-based page number.

        Returns:
            Dict with page info (size, rotation, etc.)
        """
        if page_num < 0 or page_num >= self.page_count:
            raise IndexError(f"Page {page_num} out of range (0-{self.page_count - 1})")

        page = self.doc[page_num]
        rect = page.rect
        return {
            "page_num": page_num + 1,  # 1-based for display
            "width": rect.width,
            "height": rect.height,
            "rotation": page.rotation,
        }

    def extract_text_and_bboxes(self, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract text blocks and their bounding boxes from a page.

        Each block is a dict with:
        - text: Extracted text (str)
        - bbox: (x0, y0, x1, y1) — Bounding box coordinates
        - block_type: 'text' or 'image'

        Args:
            page_num: 0-based page number.

        Returns:
            List of blocks with text and bbox.
        """
        if page_num < 0 or page_num >= self.page_count:
            raise IndexError(f"Page {page_num} out of range (0-{self.page_count - 1})")

        page = self.doc[page_num]
        blocks = []

        try:
            # Use dict_blocks to get detailed block structure
            dict_blocks = page.get_text("dict")["blocks"]

            for block in dict_blocks:
                if block["type"] == 0:  # Text block
                    text_lines = []
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text_lines.append(span["text"])

                    text = "".join(text_lines).strip()
                    if text:  # Only include non-empty blocks
                        bbox = block["bbox"]  # (x0, y0, x1, y1)
                        blocks.append({
                            "text": text,
                            "bbox": bbox,
                            "block_type": "text",
                        })

                elif block["type"] == 1:  # Image block
                    bbox = block["bbox"]
                    blocks.append({
                        "text": f"[IMAGE: {bbox[2]-bbox[0]:.0f}x{bbox[3]-bbox[1]:.0f}]",
                        "bbox": bbox,
                        "block_type": "image",
                    })

        except Exception as e:
            logger.error(f"Error extracting blocks from page {page_num + 1}: {e}")
            # Fallback: extract as plain text
            text = page.get_text()
            if text.strip():
                rect = page.rect
                blocks.append({
                    "text": text,
                    "bbox": (rect.x0, rect.y0, rect.x1, rect.y1),
                    "block_type": "text",
                })

        return blocks

    def extract_full_text(self, page_num: int) -> str:
        """
        Extract full text from a page (simple extraction).

        Args:
            page_num: 0-based page number.

        Returns:
            Extracted text as string.
        """
        if page_num < 0 or page_num >= self.page_count:
            raise IndexError(f"Page {page_num} out of range (0-{self.page_count - 1})")

        page = self.doc[page_num]
        return page.get_text()

    def get_page_image(self, page_num: int, zoom: float = 1.0) -> bytes:
        """
        Render a page to PNG image bytes.

        Args:
            page_num: 0-based page number.
            zoom: Zoom factor (1.0 = 72 DPI).

        Returns:
            PNG image bytes.
        """
        if page_num < 0 or page_num >= self.page_count:
            raise IndexError(f"Page {page_num} out of range (0-{self.page_count - 1})")

        page = self.doc[page_num]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")

    def get_document_metadata(self) -> Dict[str, Any]:
        """
        Get overall document metadata.

        Returns:
            Dict with metadata (title, author, pages, etc.)
        """
        return {
            "filename": self.pdf_path.name,
            "path": str(self.pdf_path),
            "page_count": self.page_count,
            "has_text_layer": self.has_text_layer(),
            "metadata": self.doc.metadata or {},
        }


# Top-level convenience functions for backwards compatibility

def load_pdf(pdf_path: str | Path) -> PDFHandler:
    """
    Convenience function to load a PDF.

    Args:
        pdf_path: Path to the PDF.

    Returns:
        PDFHandler instance.
    """
    return PDFHandler(pdf_path)


def extract_text_and_bboxes_from_pdf(
    pdf_path: str | Path,
    page_num: int,
) -> List[Dict[str, Any]]:
    """
    Extract text and bboxes from a single page in a PDF.

    Args:
        pdf_path: Path to the PDF.
        page_num: 0-based page number.

    Returns:
        List of blocks.
    """
    with PDFHandler(pdf_path) as handler:
        return handler.extract_text_and_bboxes(page_num)


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """Get total page count of a PDF."""
    with PDFHandler(pdf_path) as handler:
        return handler.page_count
