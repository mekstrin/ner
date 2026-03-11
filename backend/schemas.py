from pydantic import BaseModel
from typing import List, Optional


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


class EntityBase(BaseModel):
    text: str
    explanation: Optional[str] = None


class EntityCreate(EntityBase):
    category_name: str


class Entity(EntityBase):
    id: int
    category_id: int

    class Config:
        from_attributes = True


class EntityOverview(BaseModel):
    text: str
    category: str
    explanation: Optional[str] = None
    documents_count: int
    documents: List[str]


class AnalyzeRequest(BaseModel):
    text: str


class EntityExtraction(BaseModel):
    text: str
    category: str


class Prediction(BaseModel):
    start: int
    end: int
    text: str
    label: str


class AnalyzeResponse(BaseModel):
    extracted_entities: List[EntityExtraction]
    predictions: List[Prediction]


class RescanRequest(BaseModel):
    category_id: int


class RescanResponse(BaseModel):
    message: str
