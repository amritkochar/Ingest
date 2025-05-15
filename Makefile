.PHONY: install run check check-fix test lint format

install:
	poetry install

run:
	poetry run uvicorn app.main:app --reload

check: lint test typecheck

check-fix: format lint

lint:
	poetry run ruff check .

format:
	poetry run black .
	poetry run ruff format .

typecheck:
	poetry run mypy .

test:
	poetry run pytest
