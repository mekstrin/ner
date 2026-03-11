.PHONY: run-api run-ui db-up db-down init-db

run-api:
	uv run uvicorn backend.main:app

run-ui:
	uv run streamlit run frontend/app.py

db-up:
	docker-compose up -d

db-down:
	docker-compose down

init-db:
	uv run python backend/db/init_db.py
