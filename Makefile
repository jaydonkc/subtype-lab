.PHONY: dev api web test lint validate-report

dev:
	docker compose up --build

api:
	PYTHONPATH=packages/analysis-engine uvicorn analysis_engine.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

test:
	PYTHONPATH=packages/analysis-engine pytest packages/analysis-engine/tests

lint:
	PYTHONPATH=packages/analysis-engine python3 -m compileall packages/analysis-engine/analysis_engine packages/kiro-mcp-server/mcp_server

validate-report:
	python3 scripts/validate_report.py artifacts
