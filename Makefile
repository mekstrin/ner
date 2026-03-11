.PHONY: run-api run-ui db-up db-down init-db

run-api:
	uv run uvicorn backend.main:app

run-ui:
	uv run streamlit run frontend/app.py

infra-up:
	docker-compose up -d

infra-down:
	docker-compose down

init-db:
	uv run python backend/db/init_db.py
