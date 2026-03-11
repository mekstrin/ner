from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from backend.db.database import SessionLocal, engine
from backend.db import models
from backend.services import crud
from backend import schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="NER API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def background_rescan(category_id: int):
    db = SessionLocal()
    try:
        category = (
            db.query(models.Category).filter(models.Category.id == category_id).first()
        )
        if category:
            crud.rescan_texts_for_new_category(db, category)
    finally:
        db.close()


@app.get("/categories/", response_model=List[schemas.Category])
def read_categories(db: Session = Depends(get_db)):
    return crud.get_all_categories(db)


@app.post("/categories/", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.add_category(db, category.name)


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    success = crud.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}


@app.get("/entities/", response_model=List[schemas.Entity])
def read_entities(db: Session = Depends(get_db)):
    return crud.get_all_entities(db)


@app.post("/entities/", response_model=schemas.Entity)
def create_entity(entity: schemas.EntityCreate, db: Session = Depends(get_db)):
    return crud.add_entity_manual(
        db, entity.text, entity.category_name, entity.explanation
    )


@app.delete("/entities/{entity_id}")
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    success = crud.delete_entity(db, entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"message": "Entity deleted"}


@app.get("/entities/{entity_id}/overview", response_model=schemas.EntityOverview)
def read_entity_overview(
    entity_id: int, generate_explanation: bool = False, db: Session = Depends(get_db)
):
    overview = crud.get_entity_overview(db, entity_id, generate_explanation)
    if not overview:
        raise HTTPException(status_code=404, detail="Entity not found")
    return overview


@app.post("/analyze/", response_model=schemas.AnalyzeResponse)
def analyze_text(request: schemas.AnalyzeRequest, db: Session = Depends(get_db)):
    doc, extracted, predictions = crud.process_text_and_extract_entities(
        db, request.text
    )
    return {
        "extracted_entities": [
            {"text": e.text, "category": e.category.name} for e in extracted
        ],
        "predictions": predictions,
    }


@app.post("/categories/rescan", response_model=schemas.RescanResponse)
def rescan_category(
    request: schemas.RescanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    category = (
        db.query(models.Category)
        .filter(models.Category.id == request.category_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    background_tasks.add_task(background_rescan, category.id)
    return {"message": "Scan started in the background"}
