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
	if [ "$$USE_FRONTEND" = "true" ]; then \
		COMPOSE_PROFILES=frontend docker compose up --build -d; \
	else \
		docker compose up --build -d; \
	fi

down:
	docker compose down

ps:
	docker compose ps

install-cli:
	cd cli && uv tool install .

test-cli:
	cd cli && uv run pytest
