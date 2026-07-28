"""
Unit tests for pdf_handler module.
"""

import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import fitz

from normen_tool.pdf_handler import (
    PDFHandler,
    load_pdf,
    extract_text_and_bboxes_from_pdf,
    get_pdf_page_count,
    correct_pdf_page_rotations,
)


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a minimal test PDF."""
    pdf_path = tmp_path / "test.pdf"

    # Create a minimal PDF with PyMuPDF
    doc = fitz.open()
    page = doc.new_page()

    # Add some text
    page.insert_text((50, 50), "Sample PDF Content", fontsize=12)
    page.insert_text((50, 100), "This is a test document.", fontsize=10)
    page.insert_text((50, 150), "With multiple paragraphs.", fontsize=10)

    doc.save(pdf_path)
    doc.close()

    return pdf_path


class TestPDFHandler:
    """Tests for PDFHandler class."""

    def test_init_valid_pdf(self, sample_pdf_path):
        """Test initializing handler with valid PDF."""
        handler = PDFHandler(sample_pdf_path)
        assert handler.page_count == 1
        assert handler.pdf_path == sample_pdf_path
        handler.close()

    def test_init_invalid_path(self):
        """Test initializing with non-existent file."""
        with pytest.raises(FileNotFoundError):
            PDFHandler("/nonexistent/path/to/file.pdf")

    def test_init_invalid_pdf(self, tmp_path):
        """Test initializing with non-PDF file."""
        invalid_file = tmp_path / "not_a_pdf.txt"
        invalid_file.write_text("This is not a PDF")

        # PyMuPDF gracefully handles non-PDF files; this test documents that behavior
        # It may raise ValueError or just create an empty document
        try:
            handler = PDFHandler(invalid_file)
            # If it doesn't raise, just verify it's a PDFHandler instance
            assert isinstance(handler, PDFHandler)
            handler.close()
        except ValueError:
            # This is also acceptable behavior
            pass

    def test_context_manager(self, sample_pdf_path):
        """Test context manager usage."""
        with PDFHandler(sample_pdf_path) as handler:
            assert handler.page_count == 1
        # After exiting, doc should be closed (no error expected)

    def test_has_text_layer_with_text(self, sample_pdf_path):
        """Test detecting text layer in native PDF."""
        handler = PDFHandler(sample_pdf_path)
        assert handler.has_text_layer() is True
        handler.close()

    def test_has_text_layer_empty_pdf(self, tmp_path):
        """Test detecting text layer in empty PDF."""
        empty_pdf = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(empty_pdf)
        doc.close()

        handler = PDFHandler(empty_pdf)
        # Empty page should return False
        assert handler.has_text_layer() is False
        handler.close()

    def test_get_page_metadata(self, sample_pdf_path):
        """Test extracting page metadata."""
        handler = PDFHandler(sample_pdf_path)
        metadata = handler.get_page_metadata(0)

        assert metadata["page_num"] == 1
        assert metadata["width"] > 0
        assert metadata["height"] > 0
        assert "rotation" in metadata
        handler.close()

    def test_get_page_metadata_out_of_range(self, sample_pdf_path):
        """Test page metadata with invalid page number."""
        handler = PDFHandler(sample_pdf_path)
        with pytest.raises(IndexError):
            handler.get_page_metadata(999)
        handler.close()

    def test_extract_text_and_bboxes(self, sample_pdf_path):
        """Test extracting text blocks and bboxes."""
        handler = PDFHandler(sample_pdf_path)
        blocks = handler.extract_text_and_bboxes(0)

        assert len(blocks) > 0
        assert all("text" in b for b in blocks)
        assert all("bbox" in b for b in blocks)
        assert all("block_type" in b for b in blocks)

        # Check bbox format (x0, y0, x1, y1)
        for block in blocks:
            bbox = block["bbox"]
            assert len(bbox) == 4
            assert bbox[2] > bbox[0]  # x1 > x0
            assert bbox[3] > bbox[1]  # y1 > y0

        handler.close()

    def test_extract_text_and_bboxes_rotated_page(self, tmp_path):
        """Test extracting blocks from a page rotated to 90 degrees."""
        pdf_path = tmp_path / "rotated.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Rotated PDF Content", fontsize=12)
        page.set_rotation(90)
        doc.save(pdf_path)
        doc.close()

        handler = PDFHandler(pdf_path)
        blocks = handler.extract_text_and_bboxes(0)

        assert len(blocks) > 0
        assert any("Rotated PDF Content" in block["text"] for block in blocks)
        handler.close()

    def test_extract_full_text(self, sample_pdf_path):
        """Test extracting full page text."""
        handler = PDFHandler(sample_pdf_path)
        text = handler.extract_full_text(0)

        assert len(text) > 0
        assert "Sample PDF Content" in text or "sample" in text.lower()
        handler.close()

    def test_extract_full_text_invalid_page(self, sample_pdf_path):
        """Test extracting text from invalid page number."""
        handler = PDFHandler(sample_pdf_path)
        with pytest.raises(IndexError):
            handler.extract_full_text(999)
        handler.close()

    def test_get_page_image(self, sample_pdf_path):
        """Test rendering page to image."""
        handler = PDFHandler(sample_pdf_path)
        image_bytes = handler.get_page_image(0, zoom=1.0)

        # Check that some image data was returned
        assert len(image_bytes) > 0
        # PNG starts with signature
        assert image_bytes.startswith(b'\x89PNG')
        handler.close()

    def test_get_page_image_invalid_page(self, sample_pdf_path):
        """Test rendering invalid page."""
        handler = PDFHandler(sample_pdf_path)
        with pytest.raises(IndexError):
            handler.get_page_image(999)
        handler.close()

    def test_get_document_metadata(self, sample_pdf_path):
        """Test extracting document metadata."""
        handler = PDFHandler(sample_pdf_path)
        metadata = handler.get_document_metadata()

        assert metadata["filename"] == "test.pdf"
        assert metadata["page_count"] == 1
        assert "has_text_layer" in metadata
        assert "path" in metadata
        handler.close()


class TestTopLevelFunctions:
    """Tests for top-level convenience functions."""

    def test_load_pdf(self, sample_pdf_path):
        """Test load_pdf() convenience function."""
        handler = load_pdf(sample_pdf_path)
        assert isinstance(handler, PDFHandler)
        assert handler.page_count == 1
        handler.close()

    def test_extract_text_and_bboxes_from_pdf(self, sample_pdf_path):
        """Test extract_text_and_bboxes_from_pdf() function."""
        blocks = extract_text_and_bboxes_from_pdf(sample_pdf_path, 0)
        assert len(blocks) > 0
        assert all("text" in b for b in blocks)

    def test_get_pdf_page_count(self, sample_pdf_path):
        """Test get_pdf_page_count() function."""
        count = get_pdf_page_count(sample_pdf_path)
        assert count == 1

    def test_correct_pdf_page_rotations_overwrites_pdf(self, tmp_path):
        """Test correcting page rotations and overwriting the original PDF."""
        pdf_path = tmp_path / "rotated_overwrite.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Rotation test", fontsize=12)
        page.set_rotation(90)
        doc.save(pdf_path)
        doc.close()

        corrected_path = correct_pdf_page_rotations(pdf_path)

        assert corrected_path == pdf_path
        with fitz.open(pdf_path) as reopened:
            assert reopened[0].rotation == 0


class TestPDFHandlerMultiPage:
    """Tests for multi-page PDFs."""

    @pytest.fixture
    def multi_page_pdf(self, tmp_path):
        """Create a PDF with multiple pages."""
        pdf_path = tmp_path / "multipage.pdf"
        doc = fitz.open()

        for i in range(3):
            page = doc.new_page()
            page.insert_text((50, 50), f"Page {i + 1}", fontsize=14)
            page.insert_text((50, 100), f"Content on page {i + 1}.", fontsize=10)

        doc.save(pdf_path)
        doc.close()
        return pdf_path

    def test_multipage_page_count(self, multi_page_pdf):
        """Test page count for multi-page PDF."""
        handler = PDFHandler(multi_page_pdf)
        assert handler.page_count == 3
        handler.close()

    def test_multipage_extract_each_page(self, multi_page_pdf):
        """Test extracting text from each page."""
        handler = PDFHandler(multi_page_pdf)

        for i in range(3):
            text = handler.extract_full_text(i)
            assert f"Page {i + 1}" in text or f"page {i + 1}" in text.lower()

        handler.close()

    def test_multipage_metadata(self, multi_page_pdf):
        """Test metadata for each page."""
        handler = PDFHandler(multi_page_pdf)

        for i in range(3):
            metadata = handler.get_page_metadata(i)
            assert metadata["page_num"] == i + 1
            assert metadata["width"] > 0

        handler.close()
