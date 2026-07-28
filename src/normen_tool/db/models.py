"""SQLAlchemy models for database schema."""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Document(Base):
    """Represents a PDF document in a project."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    path = Column(String(512), nullable=False)
    page_count = Column(Integer, default=0)
    has_text_layer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doc_metadata = Column(JSON, nullable=True)  # Use doc_metadata instead of metadata

    # Relationship
    blocks = relationship("Block", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Document(id={self.id}, name={self.name}, pages={self.page_count})"


class Block(Base):
    """Represents a segmented text block (paragraph, section, chapter)."""

    __tablename__ = "blocks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    section = Column(String(50), nullable=True)  # e.g., "4.2.1"
    content = Column(Text, nullable=False)
    block_type = Column(String(50), default="paragraph")  # 'chapter', 'section', 'paragraph'
    pages = Column(JSON, nullable=False)  # List[int], e.g., [2, 3]
    bboxes = Column(JSON, nullable=False)  # List of bboxes per page
    page_rotations = Column(JSON, nullable=False, default=list)  # Rotation per page in degrees
    ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    document = relationship("Document", back_populates="blocks")

    def __repr__(self) -> str:
        return f"Block(id={self.id}, section={self.section}, pages={self.pages})"
