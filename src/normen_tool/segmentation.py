"""
Segmentation: Rule-based parser for extracting chapters, sections, and paragraphs from PDF text.
Handles cross-page merging and sentence boundary trimming.
"""

import logging
import re
from typing import List, Dict, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class Block:
    """Represents a single text block with metadata."""

    def __init__(
        self,
        text: str,
        bbox: Tuple[float, float, float, float],
        page_num: int,
        block_type: str = "text",
    ):
        """
        Initialize a Block.

        Args:
            text: Text content.
            bbox: Bounding box (x0, y0, x1, y1).
            page_num: 0-based page number.
            block_type: 'text' or 'image'.
        """
        self.text = text.strip()
        self.bbox = bbox
        self.page_num = page_num
        self.block_type = block_type

    def __repr__(self) -> str:
        return f"Block(page={self.page_num}, text={self.text[:30]}..., bbox={self.bbox})"


class Segment:
    """Represents a parsed segment (chapter, section, or paragraph)."""

    def __init__(
        self,
        content: str,
        section: str = "",
        segment_type: str = "paragraph",
        page_start: int = 0,
        page_end: Optional[int] = None,
        bbox_start: Optional[Tuple[float, float, float, float]] = None,
        bbox_end: Optional[Tuple[float, float, float, float]] = None,
    ):
        """
        Initialize a Segment.

        Args:
            content: Cleaned text content.
            section: Section number (e.g., "4.2.1").
            segment_type: 'chapter', 'section', or 'paragraph'.
            page_start: Starting page number (0-based).
            page_end: Ending page number (None if single page).
            bbox_start: Starting bbox.
            bbox_end: Ending bbox (for cross-page segments).
        """
        self.content = content
        self.section = section
        self.segment_type = segment_type
        self.page_start = page_start
        self.page_end = page_end if page_end is not None else page_start
        self.bbox_start = bbox_start
        self.bbox_end = bbox_end

    def __repr__(self) -> str:
        return f"Segment(section={self.section}, type={self.segment_type}, pages={self.page_start}-{self.page_end})"


# Heuristics for section detection
CHAPTER_PATTERN = re.compile(
    r"^(kapitel|chapter|section|§|article|art\.?\s*)\s*(\d+(?:\.\d+)*)",
    re.IGNORECASE,
)
SECTION_NUMBER_PATTERN = re.compile(r"^\d+(?:\.\d+)*(?:\s|$)")
SENTENCE_END_PATTERN = re.compile(r"[\.!?:;]\s*$")


class RuleBasedSegmenter:
    """Rule-based parser for extracting structured segments from PDF blocks."""

    def __init__(self, min_paragraph_length: int = 20):
        """
        Initialize segmenter.

        Args:
            min_paragraph_length: Minimum text length to be considered a block.
        """
        self.min_paragraph_length = min_paragraph_length
        self.current_section = ""

    def segment_blocks(self, blocks: List[Block]) -> List[Segment]:
        """
        Parse a list of blocks into structured segments.

        Applies heuristics for:
        - Chapter/section detection
        - Cross-page merging
        - Sentence boundary trimming

        Args:
            blocks: List of Block objects (in order, across multiple pages).

        Returns:
            List of Segment objects.
        """
        if not blocks:
            return []

        segments = []
        merged_blocks = self._merge_cross_page_blocks(blocks)

        for i, block in enumerate(merged_blocks):
            # Skip if too short or empty
            if len(block["text"]) < self.min_paragraph_length:
                logger.debug(f"Skipping short block: {block['text'][:30]}...")
                continue

            # Detect if block is a section header
            section_match = CHAPTER_PATTERN.match(block["text"])
            if section_match:
                self.current_section = section_match.group(2)
                segment_type = "chapter" if "kapitel" in section_match.group(1).lower() else "section"
            else:
                segment_type = "paragraph"

            # Trim sentence boundaries
            trimmed_text = self._trim_sentence_boundaries(block["text"])

            if len(trimmed_text) < self.min_paragraph_length:
                logger.debug(f"Skipping after boundary trim: {trimmed_text[:30]}...")
                continue

            # Create segment
            segment = Segment(
                content=trimmed_text,
                section=self.current_section,
                segment_type=segment_type,
                page_start=block.get("page_start", 0),
                page_end=block.get("page_end"),
                bbox_start=block.get("bbox_start"),
                bbox_end=block.get("bbox_end"),
            )
            segments.append(segment)

        logger.info(f"Segmented {len(blocks)} blocks into {len(segments)} segments")
        return segments

    def _merge_cross_page_blocks(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        """
        Merge blocks that span across pages based on sentence boundaries.

        If a block ends without proper sentence termination (. ! ?), 
        merge it with the next block.

        Args:
            blocks: List of Block objects.

        Returns:
            List of merged block dicts with combined text.
        """
        if not blocks:
            return []

        merged = []
        current_text = ""
        current_page_start = blocks[0].page_num
        current_bbox_start = blocks[0].bbox
        current_bbox_end = None

        for i, block in enumerate(blocks):
            current_text += (" " if current_text else "") + block.text

            # Check if we should merge with next block
            if i < len(blocks) - 1:
                next_block = blocks[i + 1]

                # If current block doesn't end with sentence punctuation, merge
                if not SENTENCE_END_PATTERN.search(block.text):
                    # Cross-page detection
                    if block.page_num != next_block.page_num:
                        logger.debug(
                            f"Cross-page merge: page {block.page_num} -> {next_block.page_num}"
                        )
                    current_bbox_end = next_block.bbox
                    continue

            # Finalize current merged block
            merged_block = {
                "text": current_text.strip(),
                "page_start": current_page_start,
                "page_end": block.page_num,
                "bbox_start": current_bbox_start,
                "bbox_end": current_bbox_end or block.bbox,
            }
            merged.append(merged_block)

            # Reset for next block
            current_text = ""
            current_page_start = blocks[i + 1].page_num if i + 1 < len(blocks) else block.page_num
            current_bbox_start = blocks[i + 1].bbox if i + 1 < len(blocks) else block.bbox
            current_bbox_end = None

        # Handle remaining text
        if current_text.strip():
            merged_block = {
                "text": current_text.strip(),
                "page_start": current_page_start,
                "page_end": blocks[-1].page_num,
                "bbox_start": current_bbox_start,
                "bbox_end": blocks[-1].bbox,
            }
            merged.append(merged_block)

        logger.debug(f"Merged {len(blocks)} blocks into {len(merged)}")
        return merged

    def _trim_sentence_boundaries(self, text: str) -> str:
        """
        Trim text to complete sentences only (ending with . ! ? : ;).

        Args:
            text: Raw text content.

        Returns:
            Trimmed text ending with proper punctuation.
        """
        # Find the last sentence-ending punctuation
        match = None
        for m in re.finditer(r"[\.!?:;]", text):
            match = m

        if match:
            return text[: match.end()].strip()

        # If no punctuation found, return original if it's short (heading/title)
        # or looks like section number
        if len(text.split()) < 8 or text.isupper():
            return text

        # Otherwise, trim to last complete word + period
        words = text.split()
        if len(words) > 1:
            return " ".join(words[:-1]) + "."

        return text

    def detect_section_number(self, text: str) -> Optional[str]:
        """
        Detect section number from text (e.g., "4.2.1" or "§123" or plain "4.2.1 Title").

        Args:
            text: Text to analyze.

        Returns:
            Section number string or None.
        """
        # First, try pattern with keywords
        match = CHAPTER_PATTERN.match(text)
        if match:
            return match.group(2)

        # Try plain section number pattern (e.g., "4.2.1 Title")
        section_match = SECTION_NUMBER_PATTERN.match(text)
        if section_match:
            return section_match.group(0).strip()

        return None


# Top-level convenience functions

def segment_pdf_blocks(
    blocks: List[Tuple[str, Tuple[float, float, float, float], int]],
) -> List[Segment]:
    """
    Convenience function to segment PDF blocks.

    Args:
        blocks: List of (text, bbox, page_num) tuples.

    Returns:
        List of Segment objects.
    """
    block_objs = [
        Block(text=text, bbox=bbox, page_num=page_num)
        for text, bbox, page_num in blocks
    ]
    segmenter = RuleBasedSegmenter()
    return segmenter.segment_blocks(block_objs)


def merge_cross_page_blocks(
    blocks: List[Tuple[str, Tuple[float, float, float, float], int]],
) -> List[Dict[str, Any]]:
    """
    Convenience function to merge cross-page blocks.

    Args:
        blocks: List of (text, bbox, page_num) tuples.

    Returns:
        List of merged block dicts.
    """
    block_objs = [
        Block(text=text, bbox=bbox, page_num=page_num)
        for text, bbox, page_num in blocks
    ]
    segmenter = RuleBasedSegmenter()
    return segmenter._merge_cross_page_blocks(block_objs)
