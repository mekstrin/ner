from sqlalchemy.orm import Session
from backend.db.models import Category, Entity, Document
from backend.services.ml_service import ner_model
from backend.services.llm_service import llm_service


def get_all_categories(db: Session):
    return db.query(Category).all()


def add_category(db: Session, name: str):
    category = db.query(Category).filter(Category.name == name).first()
    if not category:
        category = Category(name=name)
        db.add(category)
        db.commit()
        db.refresh(category)
    return category


def delete_category(db: Session, category_id: int):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        db.delete(category)
        db.commit()
        return True
    return False


def get_all_entities(db: Session):
    return db.query(Entity).all()


def add_entity_manual(
    db: Session, text: str, category_name: str, explanation: str = None
):
    category = add_category(db, category_name)
    entity = db.query(Entity).filter(Entity.text == text.lower()).first()
    if not entity:
        entity = Entity(
            text=text.lower(), category_id=category.id, explanation=explanation
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
    return entity


def delete_entity(db: Session, entity_id: int):
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if entity:
        db.delete(entity)
        db.commit()
        return True
    return False


def process_text_and_extract_entities(db: Session, text: str):
    doc = Document(content=text)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    categories = get_all_categories(db)
    labels = [c.name for c in categories]

    if not labels:
        return doc, [], []

    predictions = ner_model.predict(text, labels)

    extracted_entities = []
    for pred in predictions:
        entity_text = pred["text"].lower()
        label = pred["label"]

        cat = next((c for c in categories if c.name == label), None)
        if not cat:
            continue

        entity = db.query(Entity).filter(Entity.text == entity_text).first()
        if not entity:
            entity = Entity(text=entity_text, category_id=cat.id, explanation=None)
            db.add(entity)
            db.commit()
            db.refresh(entity)

        if entity not in doc.entities:
            doc.entities.append(entity)

        extracted_entities.append(entity)

    db.commit()
    return doc, extracted_entities, predictions


def rescan_texts_for_new_category(db: Session, new_category: Category):
    documents = db.query(Document).all()
    labels = [new_category.name]

    new_entities_count = 0

    for doc in documents:
        predictions = ner_model.predict(doc.content, labels)
        for pred in predictions:
            entity_text = pred["text"].lower()

            entity = db.query(Entity).filter(Entity.text == entity_text).first()
            if not entity:
                entity = Entity(
                    text=entity_text,
                    category_id=new_category.id,
                    explanation=None,
                )
                db.add(entity)
                db.commit()
                db.refresh(entity)
                new_entities_count += 1

            if entity not in doc.entities:
                doc.entities.append(entity)

    db.commit()
    return new_entities_count


def get_entity_overview(
    db: Session, entity_id: int, generate_explanation: bool = False
):
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        return None

    if generate_explanation and not entity.explanation:
        context = "\n".join([d.content for d in entity.documents][:5]) if entity.documents else None  # Ограничиваем контекст первыми 5 документами
        explanation = llm_service.get_explanation(entity.text, context=context)
        entity.explanation = explanation
        db.commit()
        db.refresh(entity)

    return {
        "text": entity.text,
        "category": entity.category.name,
        "explanation": entity.explanation,
        "documents_count": len(entity.documents),
        "documents": [d.content for d in entity.documents],
    }
