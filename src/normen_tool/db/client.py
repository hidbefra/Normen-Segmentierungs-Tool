"""Database client for CRUD operations."""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session

from normen_tool.db.models import Base, Document, Block

logger = logging.getLogger(__name__)


class DBClient:
    """Client for database operations."""

    def __init__(self, db_path: str | Path):
        """
        Initialize database client.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def init_db(self) -> None:
        """
        Initialize database (create tables if not exist).
        """
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {self.db_path}")

    def clear_db(self) -> None:
        """
        Clear all tables. Useful for testing.
        """
        Base.metadata.drop_all(self.engine)
        logger.warning("Database cleared")

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    # ========== Document Operations ==========

    def add_document(
        self,
        name: str,
        path: str,
        page_count: int = 0,
        has_text_layer: bool = False,
        doc_metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """
        Add a new document to the database.

        Args:
            name: Document name (e.g., filename).
            path: Full path to document.
            page_count: Number of pages.
            has_text_layer: Whether document has OCR text layer.
            doc_metadata: Additional metadata (dict).

        Returns:
            Created Document object.
        """
        session = self._get_session()
        try:
            doc = Document(
                name=name,
                path=path,
                page_count=page_count,
                has_text_layer=has_text_layer,
                doc_metadata=doc_metadata,
            )
            session.add(doc)
            session.commit()
            doc_id = doc.id  # Get ID before closing session
            logger.info(f"Added document: {name}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding document: {e}")
            raise
        finally:
            session.close()

        # Reload the document from database to avoid detached instance issues
        return self.get_document(doc_id)

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        session = self._get_session()
        try:
            return session.query(Document).filter(Document.id == doc_id).first()
        finally:
            session.close()

    def get_document_by_name(self, name: str) -> Optional[Document]:
        """Get document by name."""
        session = self._get_session()
        try:
            return session.query(Document).filter(Document.name == name).first()
        finally:
            session.close()

    def list_documents(self) -> List[Document]:
        """List all documents."""
        session = self._get_session()
        try:
            return session.query(Document).all()
        finally:
            session.close()

    def update_document(
        self,
        doc_id: str,
        **kwargs: Any,
    ) -> Optional[Document]:
        """
        Update document properties.

        Args:
            doc_id: Document ID.
            **kwargs: Fields to update (name, page_count, has_text_layer, etc.).

        Returns:
            Updated Document or None if not found.
        """
        session = self._get_session()
        doc_id_result = None
        try:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if doc:
                for key, value in kwargs.items():
                    if hasattr(doc, key):
                        setattr(doc, key, value)
                doc.modified_at = datetime.utcnow()
                session.commit()
                doc_id_result = doc.id  # Capture ID before closing
                logger.info(f"Updated document: {doc_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating document: {e}")
            raise
        finally:
            session.close()

        # Reload to avoid detached instance
        return self.get_document(doc_id_result) if doc_id_result else None

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document and all associated blocks.

        Args:
            doc_id: Document ID.

        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        try:
            doc = session.query(Document).filter(Document.id == doc_id).first()
            if doc:
                session.delete(doc)
                session.commit()
                logger.info(f"Deleted document: {doc_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting document: {e}")
            raise
        finally:
            session.close()

    # ========== Block Operations ==========

    def add_block(
        self,
        document_id: str,
        content: str,
        section: str = "",
        block_type: str = "paragraph",
        pages: Optional[List[int]] = None,
        bboxes: Optional[List[tuple]] = None,
        ai_generated: bool = False,
    ) -> Block:
        """
        Add a new block to the database.

        Args:
            document_id: Parent document ID.
            content: Block text content.
            section: Section number (e.g., "4.2.1").
            block_type: 'chapter', 'section', or 'paragraph'.
            pages: List of page numbers block spans.
            bboxes: List of bounding boxes.
            ai_generated: Whether generated by AI.

        Returns:
            Created Block object.
        """
        if pages is None:
            pages = [0]
        if bboxes is None:
            bboxes = [(0, 0, 100, 100)]

        session = self._get_session()
        block_id = None
        try:
            block = Block(
                document_id=document_id,
                content=content,
                section=section,
                block_type=block_type,
                pages=pages,
                bboxes=bboxes,
                ai_generated=ai_generated,
            )
            session.add(block)
            session.commit()
            block_id = block.id
            logger.info(f"Added block: {block_id[:8]}... to doc {document_id[:8]}...")
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding block: {e}")
            raise
        finally:
            session.close()

        # Reload to avoid detached instance
        return self.get_block(block_id)

    def get_block(self, block_id: str) -> Optional[Block]:
        """Get block by ID."""
        session = self._get_session()
        try:
            return session.query(Block).filter(Block.id == block_id).first()
        finally:
            session.close()

    def list_blocks(self, document_id: str) -> List[Block]:
        """List all blocks for a document."""
        session = self._get_session()
        try:
            return session.query(Block).filter(Block.document_id == document_id).all()
        finally:
            session.close()

    def list_blocks_by_section(self, document_id: str, section: str) -> List[Block]:
        """List blocks for a specific section."""
        session = self._get_session()
        try:
            return session.query(Block).filter(
                Block.document_id == document_id,
                Block.section == section,
            ).all()
        finally:
            session.close()

    def update_block(
        self,
        block_id: str,
        **kwargs: Any,
    ) -> Optional[Block]:
        """
        Update block properties.

        Args:
            block_id: Block ID.
            **kwargs: Fields to update (content, section, block_type, etc.).

        Returns:
            Updated Block or None if not found.
        """
        session = self._get_session()
        block_id_result = None
        try:
            block = session.query(Block).filter(Block.id == block_id).first()
            if block:
                for key, value in kwargs.items():
                    if hasattr(block, key) and key not in ("id", "document_id", "created_at"):
                        setattr(block, key, value)
                block.modified_at = datetime.utcnow()
                session.commit()
                block_id_result = block.id  # Capture ID before closing
                logger.info(f"Updated block: {block_id[:8]}...")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating block: {e}")
            raise
        finally:
            session.close()

        # Reload to avoid detached instance
        return self.get_block(block_id_result) if block_id_result else None

    def delete_block(self, block_id: str) -> bool:
        """
        Delete a block.

        Args:
            block_id: Block ID.

        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        try:
            block = session.query(Block).filter(Block.id == block_id).first()
            if block:
                session.delete(block)
                session.commit()
                logger.info(f"Deleted block: {block_id[:8]}...")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting block: {e}")
            raise
        finally:
            session.close()

    # ========== Batch Operations ==========

    def bulk_insert_blocks(
        self,
        document_id: str,
        blocks_data: List[Dict[str, Any]],
    ) -> List[Block]:
        """
        Insert multiple blocks at once.

        Args:
            document_id: Parent document ID.
            blocks_data: List of block data dicts (content, section, block_type, pages, bboxes, ai_generated).

        Returns:
            List of created Block objects.
        """
        session = self._get_session()
        try:
            blocks = []
            for block_data in blocks_data:
                block = Block(
                    document_id=document_id,
                    **block_data,
                )
                session.add(block)
                blocks.append(block)

            session.commit()
            
            # Force SQLAlchemy to populate IDs after commit
            session.flush()
            
            # Capture IDs and data while session is still open
            block_data_list = [
                {"id": b.id, "content": b.content, "section": b.section, 
                 "document_id": b.document_id, "block_type": b.block_type, 
                 "pages": b.pages, "bboxes": b.bboxes, "ai_generated": b.ai_generated,
                 "created_at": b.created_at, "modified_at": b.modified_at}
                for b in blocks
            ]
            logger.info(f"Bulk inserted {len(block_data_list)} blocks")
        except Exception as e:
            session.rollback()
            logger.error(f"Error bulk inserting blocks: {e}")
            raise
        finally:
            session.close()

        # Reload blocks in new session to avoid detached instances
        return [self.get_block(bdata["id"]) for bdata in block_data_list]

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        session = self._get_session()
        try:
            doc_count = session.query(Document).count()
            block_count = session.query(Block).count()
            avg_blocks_per_doc = block_count / doc_count if doc_count > 0 else 0

            return {
                "documents": doc_count,
                "blocks": block_count,
                "avg_blocks_per_document": avg_blocks_per_doc,
            }
        finally:
            session.close()
