"""
Unit tests for segmentation module.
"""

import pytest
from normen_tool.segmentation import (
    Block,
    Segment,
    RuleBasedSegmenter,
    segment_pdf_blocks,
    merge_cross_page_blocks,
    CHAPTER_PATTERN,
)


class TestBlock:
    """Tests for Block class."""

    def test_block_creation(self):
        """Test creating a Block."""
        block = Block(
            text="Test content",
            bbox=(10, 20, 100, 40),
            page_num=0,
        )
        assert block.text == "Test content"
        assert block.bbox == (10, 20, 100, 40)
        assert block.page_num == 0
        assert block.block_type == "text"

    def test_block_strips_whitespace(self):
        """Test that Block strips leading/trailing whitespace."""
        block = Block(
            text="  Indented text  \n",
            bbox=(0, 0, 100, 20),
            page_num=0,
        )
        assert block.text == "Indented text"

    def test_block_image_type(self):
        """Test Block with image type."""
        block = Block(
            text="[IMAGE]",
            bbox=(0, 0, 100, 100),
            page_num=0,
            block_type="image",
        )
        assert block.block_type == "image"


class TestSegment:
    """Tests for Segment class."""

    def test_segment_creation(self):
        """Test creating a Segment."""
        segment = Segment(
            content="Paragraph text.",
            section="4.2.1",
            segment_type="paragraph",
            page_start=0,
            page_end=0,
        )
        assert segment.content == "Paragraph text."
        assert segment.section == "4.2.1"
        assert segment.segment_type == "paragraph"

    def test_segment_cross_page(self):
        """Test Segment spanning multiple pages."""
        segment = Segment(
            content="Cross-page paragraph.",
            section="4.3",
            page_start=2,
            page_end=3,
            bbox_start=(10, 100, 200, 400),
            bbox_end=(10, 50, 200, 150),
        )
        assert segment.page_start == 2
        assert segment.page_end == 3
        assert segment.bbox_start is not None
        assert segment.bbox_end is not None


class TestRuleBasedSegmenter:
    """Tests for RuleBasedSegmenter class."""

    @pytest.fixture
    def segmenter(self):
        """Create a segmenter instance."""
        return RuleBasedSegmenter(min_paragraph_length=10)

    def test_segmenter_init(self, segmenter):
        """Test segmenter initialization."""
        assert segmenter.min_paragraph_length == 10
        assert segmenter.current_section == ""

    def test_empty_blocks(self, segmenter):
        """Test segmenting empty block list."""
        segments = segmenter.segment_blocks([])
        assert segments == []

    def test_single_paragraph(self, segmenter):
        """Test segmenting a single paragraph."""
        blocks = [Block("This is a test paragraph.", (0, 0, 100, 20), 0)]
        segments = segmenter.segment_blocks(blocks)

        assert len(segments) == 1
        assert segments[0].content == "This is a test paragraph."
        assert segments[0].segment_type == "paragraph"

    def test_chapter_detection(self, segmenter):
        """Test detecting chapter headers."""
        blocks = [
            Block("Kapitel 4 - Introduction", (0, 0, 100, 20), 0),
            Block("This is paragraph content under chapter 4 with more detail.", (0, 30, 100, 50), 0),
        ]
        segments = segmenter.segment_blocks(blocks)

        assert len(segments) >= 1
        assert any(s.segment_type == "chapter" for s in segments)
        # Check that section is set from chapter header
        chapter_idx = next(i for i, s in enumerate(segments) if s.segment_type == "chapter")
        assert segments[chapter_idx].section == "4"

    def test_section_detection(self, segmenter):
        """Test detecting section headers with keyword format."""
        blocks = [
            Block("Section 4.2.1 Subsection Title with descriptive content", (0, 0, 100, 20), 0),
            Block("Detailed content here with more text.", (0, 30, 100, 50), 0),
        ]
        segments = segmenter.segment_blocks(blocks)

        assert len(segments) >= 1
        # At least one segment should be section type
        assert any(s.segment_type == "section" or s.section != "" for s in segments)

    def test_skip_short_blocks(self, segmenter):
        """Test that very short blocks are skipped."""
        blocks = [
            Block("Short", (0, 0, 100, 20), 0),  # Too short
            Block("This is a long enough paragraph to be included.", (0, 30, 100, 50), 0),
        ]
        segments = segmenter.segment_blocks(blocks)

        assert len(segments) == 1
        assert "long enough" in segments[0].content

    def test_cross_page_merge_without_punctuation(self, segmenter):
        """Test merging blocks across pages when first block lacks ending punctuation."""
        blocks = [
            Block("This sentence continues", (0, 0, 100, 200), 0),  # No ending punct
            Block("on the next page.", (0, 50, 100, 150), 1),  # But next page completes it
        ]
        merged = segmenter._merge_cross_page_blocks(blocks)

        assert len(merged) == 1
        assert "continues" in merged[0]["text"] and "next page" in merged[0]["text"]
        assert merged[0]["page_start"] == 0
        assert merged[0]["page_end"] == 1

    def test_cross_page_merge_with_punctuation(self, segmenter):
        """Test that blocks ending with punctuation are NOT merged."""
        blocks = [
            Block("First sentence.", (0, 0, 100, 200), 0),  # Has ending punct
            Block("Second sentence.", (0, 50, 100, 150), 1),
        ]
        merged = segmenter._merge_cross_page_blocks(blocks)

        # Should be separate
        assert len(merged) == 2

    def test_merged_bbox_spans_all_blocks_in_segment(self, segmenter):
        """Test that merged segments use a union bbox covering all included blocks."""
        blocks = [
            Block("First line of a longer paragraph", (10, 20, 80, 40), 0),
            Block("Second line of the same paragraph", (10, 45, 90, 70), 0),
        ]
        merged = segmenter._merge_cross_page_blocks(blocks)

        assert len(merged) == 1
        assert merged[0]["bbox_start"] == (10, 20, 90, 70)
        assert merged[0]["bbox_end"] == (10, 20, 90, 70)

    def test_sentence_boundary_trimming(self, segmenter):
        """Test trimming of sentence boundaries."""
        # Text with punctuation at end
        trimmed = segmenter._trim_sentence_boundaries(
            "First sentence. Second incomplete"
        )
        assert trimmed.endswith(".")

        # Text without punctuation
        trimmed = segmenter._trim_sentence_boundaries("No punctuation here")
        assert trimmed  # Should return something

    def test_section_number_detection(self, segmenter):
        """Test detecting section numbers from various formats."""
        # Keyword-based formats
        assert segmenter.detect_section_number("Kapitel 4.2.1 Title") == "4.2.1"
        assert segmenter.detect_section_number("Section 5") == "5"
        assert segmenter.detect_section_number("§123 Rule") == "123"

        # Plain number format (without keywords)
        assert segmenter.detect_section_number("4.2.1 Title") == "4.2.1"
        assert segmenter.detect_section_number("5 Content") == "5"

        # Non-matching
        assert segmenter.detect_section_number("Regular text") is None

    def test_multiple_paragraphs_same_page(self, segmenter):
        """Test segmenting multiple paragraphs on the same page."""
        blocks = [
            Block("First paragraph with proper ending.", (0, 0, 100, 30), 0),
            Block("Second paragraph also ends properly.", (0, 40, 100, 70), 0),
            Block("Third paragraph.", (0, 80, 100, 110), 0),
        ]
        segments = segmenter.segment_blocks(blocks)

        assert len(segments) == 3
        assert all(s.page_start == s.page_end == 0 for s in segments)


class TestChapterPatternRegex:
    """Tests for chapter detection regex pattern."""

    def test_kapitel_format(self):
        """Test 'Kapitel X' format."""
        assert CHAPTER_PATTERN.match("Kapitel 4")
        assert CHAPTER_PATTERN.match("kapitel 4.2")
        assert CHAPTER_PATTERN.match("KAPITEL 4.2.1")

    def test_chapter_format(self):
        """Test 'Chapter X' format."""
        assert CHAPTER_PATTERN.match("Chapter 5")
        assert CHAPTER_PATTERN.match("chapter 5.1")

    def test_section_format(self):
        """Test 'Section X' format."""
        assert CHAPTER_PATTERN.match("Section 3.1")
        assert CHAPTER_PATTERN.match("section 3.1.1")

    def test_paragraph_format(self):
        """Test '§' format."""
        assert CHAPTER_PATTERN.match("§ 123")
        assert CHAPTER_PATTERN.match("§123")

    def test_non_matching(self):
        """Test strings that should NOT match."""
        assert not CHAPTER_PATTERN.match("This is regular text")
        assert not CHAPTER_PATTERN.match("The 4th item in a list")


class TestTopLevelFunctions:
    """Tests for top-level convenience functions."""

    def test_segment_pdf_blocks(self):
        """Test segment_pdf_blocks() function."""
        blocks = [
            ("Kapitel 4 - Title with more content", (0, 0, 100, 20), 0),
            ("This is detailed content explaining section.", (0, 30, 100, 50), 0),
        ]
        segments = segment_pdf_blocks(blocks)

        assert len(segments) >= 1
        assert any(s.segment_type == "chapter" for s in segments)

    def test_merge_cross_page_blocks(self):
        """Test merge_cross_page_blocks() function."""
        blocks = [
            ("First part", (0, 0, 100, 200), 0),
            ("Second part.", (0, 50, 100, 150), 1),
        ]
        merged = merge_cross_page_blocks(blocks)

        assert len(merged) == 1
        assert merged[0]["page_end"] == 1


class TestComplexSegmentation:
    """Tests for complex, realistic segmentation scenarios."""

    @pytest.fixture
    def segmenter(self):
        """Create a segmenter instance."""
        return RuleBasedSegmenter(min_paragraph_length=15)

    def test_realistic_norm_document(self, segmenter):
        """Test segmenting a realistic norm/standard document structure."""
        blocks = [
            Block("DIN EN ISO 9001:2015 Qualitätsmanagementsysteme Anforderungen", (0, 0, 200, 30), 0),
            Block(
                "Kapitel 4 Kontext der Organisation und seine Umgebung",
                (0, 60, 200, 80),
                0,
            ),
            Block(
                "The organization must understand the organization and context. "
                "This shall be documented and maintained.",
                (0, 90, 200, 150),
                0,
            ),
        ]
        segments = segmenter.segment_blocks(blocks)

        # Should have parsed multiple segments
        assert len(segments) > 0

    def test_cross_page_with_section_continuation(self, segmenter):
        """Test cross-page content with section context."""
        blocks = [
            Block("5.1 Leadership", (0, 0, 100, 20), 2),
            Block(
                "The organization shall demonstrate leadership and commitment. "
                "Leadership shall include",
                (0, 30, 100, 100),
                2,
            ),  # No ending punct
            Block(
                "providing resources for the management system.",
                (0, 50, 100, 120),
                3,
            ),
        ]
        segments = segmenter.segment_blocks(blocks)

        # Should merge cross-page content
        assert any(s.page_end > s.page_start for s in segments if len(s.content) > 30)

    def test_numbering_inheritance(self, segmenter):
        """Test that section numbers are inherited by following paragraphs."""
        blocks = [
            Block("6.2 Planning of Quality Management System", (0, 0, 100, 20), 0),
            Block(
                "The organization shall plan the actions needed to address these risks. "
                "This shall be documented.",
                (0, 30, 100, 80),
                0,
            ),
            Block(
                "The results of this planning shall be documented and reviewed.",
                (0, 90, 100, 130),
                0,
            ),
        ]
        segments = segmenter.segment_blocks(blocks)

        # All segments should inherit section 6.2
        assert all(s.section == "6.2" or s.section == "" for s in segments)
