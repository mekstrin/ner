from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

document_entity_association = Table(
    "document_entities",
    Base.metadata,
    Column("document_id", Integer, ForeignKey("documents.id"), primary_key=True),
    Column("entity_id", Integer, ForeignKey("entities.id"), primary_key=True),
    Column("role", String, nullable=True),
)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    entities = relationship(
        "Entity", back_populates="category", cascade="all, delete-orphan"
    )


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False, unique=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="entities")
    documents = relationship(
        "Document", secondary=document_entity_association, back_populates="entities"
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    entities = relationship(
        "Entity", secondary=document_entity_association, back_populates="documents"
    )
