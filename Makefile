.PHONY: bootstrap test-backend run-backend migrate up down ps

bootstrap:
	./scripts/bootstrap.sh

test-backend:
	cd backend && uv run pytest

run-backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	docker compose run --rm migrations

up:
	docker compose up --build -d

down:
	docker compose down

ps:
	docker compose ps
