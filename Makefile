.PHONY: install corpus up-infra ingest api web mcp bot test lint eval up down dataset train
PY ?= python
install:
	cd backend && $(PY) -m pip install -e ".[dev]"
	cd frontend && pnpm install
corpus:
	$(PY) data/generator/generate_corpus.py
up-infra:
	docker compose up -d qdrant postgres minio
ingest:
	cd backend && $(PY) -m app.ingestion.run_ingestion --corpus ../data/corpus
api:
	cd backend && uvicorn app.main:app --reload --port 8000
web:
	cd frontend && pnpm dev
mcp:
	cd backend && $(PY) -m app.mcp_server.server
bot:
	cd backend && $(PY) -m app.bot.main
test:
	cd backend && $(PY) -m pytest -q
	cd frontend && pnpm test
lint:
	ruff check backend && cd backend && mypy app
eval:
	cd backend && $(PY) ../eval/scripts/run_eval.py
dataset:
	$(PY) training/build_dataset.py && $(PY) training/verify_dataset.py
train:
	$(PY) training/reranker/train_reranker.py
up:
	docker compose up --build -d
down:
	docker compose down
