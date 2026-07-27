"""Unit tests for database module."""

import pytest
import tempfile
from pathlib import Path

from normen_tool.db.client import DBClient
from normen_tool.db.models import Document, Block


@pytest.fixture
def db_path():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    # Cleanup
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def db_client(db_path):
    """Create and initialize a DB client."""
    client = DBClient(db_path)
    client.init_db()
    yield client
    # Cleanup
    client.clear_db()
    client.engine.dispose()  # Close all connections


class TestDocumentOperations:
    """Tests for document CRUD operations."""

    def test_add_document(self, db_client):
        """Test adding a document."""
        doc = db_client.add_document(
            name="test.pdf",
            path="/path/to/test.pdf",
            page_count=10,
            has_text_layer=True,
        )

        assert doc is not None
        assert doc.name == "test.pdf"
        assert doc.page_count == 10
        assert doc.has_text_layer is True

    def test_get_document_by_id(self, db_client):
        """Test retrieving document by ID."""
        doc = db_client.add_document("test.pdf", "/path/to/test.pdf", page_count=5)
        retrieved = db_client.get_document(doc.id)

        assert retrieved is not None
        assert retrieved.id == doc.id
        assert retrieved.name == "test.pdf"

    def test_get_document_by_name(self, db_client):
        """Test retrieving document by name."""
        doc = db_client.add_document("test.pdf", "/path/to/test.pdf")
        retrieved = db_client.get_document_by_name("test.pdf")

        assert retrieved is not None
        assert retrieved.id == doc.id

    def test_list_documents(self, db_client):
        """Test listing all documents."""
        db_client.add_document("doc1.pdf", "/path/doc1.pdf")
        db_client.add_document("doc2.pdf", "/path/doc2.pdf")
        db_client.add_document("doc3.pdf", "/path/doc3.pdf")

        docs = db_client.list_documents()
        assert len(docs) == 3

    def test_update_document(self, db_client):
        """Test updating document properties."""
        doc = db_client.add_document("test.pdf", "/path/test.pdf", page_count=5)
        updated = db_client.update_document(doc.id, page_count=15, has_text_layer=True)

        assert updated is not None
        assert updated.page_count == 15
        assert updated.has_text_layer is True

    def test_delete_document(self, db_client):
        """Test deleting a document."""
        doc = db_client.add_document("test.pdf", "/path/test.pdf")
        deleted = db_client.delete_document(doc.id)

        assert deleted is True
        retrieved = db_client.get_document(doc.id)
        assert retrieved is None

    def test_delete_nonexistent_document(self, db_client):
        """Test deleting non-existent document."""
        deleted = db_client.delete_document("nonexistent-id")
        assert deleted is False


class TestBlockOperations:
    """Tests for block CRUD operations."""

    @pytest.fixture
    def doc(self, db_client):
        """Create a test document."""
        return db_client.add_document("test.pdf", "/path/test.pdf", page_count=10)

    def test_add_block(self, db_client, doc):
        """Test adding a block."""
        block = db_client.add_block(
            document_id=doc.id,
            content="This is a test paragraph.",
            section="4.1",
            block_type="paragraph",
            pages=[0],
            bboxes=[(10, 20, 100, 40)],
        )

        assert block is not None
        assert block.content == "This is a test paragraph."
        assert block.section == "4.1"
        assert block.pages == [0]

    def test_get_block_by_id(self, db_client, doc):
        """Test retrieving block by ID."""
        block = db_client.add_block(
            document_id=doc.id,
            content="Test content.",
            section="4.1",
        )
        retrieved = db_client.get_block(block.id)

        assert retrieved is not None
        assert retrieved.id == block.id
        assert retrieved.content == "Test content."

    def test_list_blocks_by_document(self, db_client, doc):
        """Test listing blocks for a document."""
        db_client.add_block(doc.id, "Block 1", section="4.1")
        db_client.add_block(doc.id, "Block 2", section="4.2")
        db_client.add_block(doc.id, "Block 3", section="4.1")

        blocks = db_client.list_blocks(doc.id)
        assert len(blocks) == 3

    def test_list_blocks_by_section(self, db_client, doc):
        """Test listing blocks by section."""
        db_client.add_block(doc.id, "Block A", section="4.1")
        db_client.add_block(doc.id, "Block B", section="4.2")
        db_client.add_block(doc.id, "Block C", section="4.1")

        blocks = db_client.list_blocks_by_section(doc.id, "4.1")
        assert len(blocks) == 2
        assert all(b.section == "4.1" for b in blocks)

    def test_update_block(self, db_client, doc):
        """Test updating a block."""
        block = db_client.add_block(
            document_id=doc.id,
            content="Original content.",
            section="4.1",
        )
        updated = db_client.update_block(
            block.id,
            content="Updated content.",
            section="4.2",
        )

        assert updated is not None
        assert updated.content == "Updated content."
        assert updated.section == "4.2"

    def test_delete_block(self, db_client, doc):
        """Test deleting a block."""
        block = db_client.add_block(doc.id, "Test block content.")
        deleted = db_client.delete_block(block.id)

        assert deleted is True
        retrieved = db_client.get_block(block.id)
        assert retrieved is None

    def test_delete_nonexistent_block(self, db_client):
        """Test deleting non-existent block."""
        deleted = db_client.delete_block("nonexistent-id")
        assert deleted is False


class TestBulkOperations:
    """Tests for bulk insert operations."""

    @pytest.fixture
    def doc(self, db_client):
        """Create a test document."""
        return db_client.add_document("test.pdf", "/path/test.pdf")

    def test_bulk_insert_blocks(self, db_client, doc):
        """Test bulk inserting blocks."""
        blocks_data = [
            {
                "content": "Block 1",
                "section": "4.1",
                "block_type": "paragraph",
                "pages": [0],
                "bboxes": [(0, 0, 100, 20)],
            },
            {
                "content": "Block 2",
                "section": "4.2",
                "block_type": "paragraph",
                "pages": [1],
                "bboxes": [(0, 0, 100, 20)],
            },
            {
                "content": "Block 3",
                "section": "4.2",
                "block_type": "paragraph",
                "pages": [1, 2],
                "bboxes": [(0, 0, 100, 20), (0, 0, 100, 30)],
            },
        ]

        blocks = db_client.bulk_insert_blocks(doc.id, blocks_data)
        assert len(blocks) == 3
        assert all(b.document_id == doc.id for b in blocks)

    def test_bulk_insert_empty_list(self, db_client, doc):
        """Test bulk inserting empty list."""
        blocks = db_client.bulk_insert_blocks(doc.id, [])
        assert len(blocks) == 0


class TestCascadingDelete:
    """Tests for cascading delete behavior."""

    def test_delete_document_cascades_blocks(self, db_client):
        """Test that deleting a document deletes its blocks."""
        doc = db_client.add_document("test.pdf", "/path/test.pdf")
        block1 = db_client.add_block(doc.id, "Block 1")
        block2 = db_client.add_block(doc.id, "Block 2")

        # Delete document
        db_client.delete_document(doc.id)

        # Blocks should also be deleted
        assert db_client.get_block(block1.id) is None
        assert db_client.get_block(block2.id) is None


class TestStatistics:
    """Tests for database statistics."""

    def test_get_statistics(self, db_client):
        """Test getting database statistics."""
        doc1 = db_client.add_document("doc1.pdf", "/path/doc1.pdf")
        doc2 = db_client.add_document("doc2.pdf", "/path/doc2.pdf")

        db_client.add_block(doc1.id, "Block 1")
        db_client.add_block(doc1.id, "Block 2")
        db_client.add_block(doc2.id, "Block 3")

        stats = db_client.get_statistics()

        assert stats["documents"] == 2
        assert stats["blocks"] == 3
        assert stats["avg_blocks_per_document"] == 1.5

    def test_statistics_empty_db(self, db_client):
        """Test statistics on empty database."""
        stats = db_client.get_statistics()

        assert stats["documents"] == 0
        assert stats["blocks"] == 0
        assert stats["avg_blocks_per_document"] == 0


class TestComplexScenarios:
    """Tests for complex, realistic scenarios."""

    def test_document_with_multiple_blocks_across_pages(self, db_client):
        """Test document with blocks spanning multiple pages."""
        doc = db_client.add_document("norm.pdf", "/path/norm.pdf", page_count=10)

        # Add blocks spanning pages
        block1 = db_client.add_block(
            doc.id,
            "Section 4: Context",
            section="4",
            block_type="chapter",
            pages=[0],
            bboxes=[(10, 20, 200, 40)],
        )

        block2 = db_client.add_block(
            doc.id,
            "This paragraph continues from page 2 to page 3 with detailed content.",
            section="4.1",
            block_type="paragraph",
            pages=[2, 3],
            bboxes=[(10, 50, 200, 300), (10, 20, 200, 150)],
        )

        block3 = db_client.add_block(
            doc.id,
            "Another section on page 5.",
            section="5",
            block_type="chapter",
            pages=[5],
            bboxes=[(10, 30, 200, 50)],
        )

        # Verify
        blocks = db_client.list_blocks(doc.id)
        assert len(blocks) == 3

        # Check chapters
        chapters = db_client.list_blocks_by_section(doc.id, "4")
        assert len(chapters) == 1
        assert chapters[0].block_type == "chapter"

        # Check cross-page blocks
        assert block2.pages == [2, 3]
        assert len(block2.bboxes) == 2

    def test_update_document_metadata(self, db_client):
        """Test updating document with metadata."""
        doc_metadata = {
            "original_title": "DIN EN ISO 9001:2015",
            "language": "de",
            "ocr_engine": "pytesseract",
        }

        doc = db_client.add_document(
            "standard.pdf",
            "/path/standard.pdf",
            page_count=50,
            doc_metadata=doc_metadata,
        )

        retrieved = db_client.get_document(doc.id)
        assert retrieved.doc_metadata == doc_metadata
        assert retrieved.doc_metadata["original_title"] == "DIN EN ISO 9001:2015"
