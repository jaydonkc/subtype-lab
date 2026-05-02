FROM python:3.12-slim

WORKDIR /app
COPY packages/analysis-engine/requirements.txt /app/analysis-requirements.txt
COPY packages/kiro-mcp-server/requirements.txt /app/mcp-requirements.txt
RUN pip install --no-cache-dir -r /app/analysis-requirements.txt -r /app/mcp-requirements.txt
COPY packages/analysis-engine/analysis_engine /app/analysis_engine
COPY packages/kiro-mcp-server/mcp_server /app/mcp_server
ENV PYTHONPATH=/app
CMD ["python", "-m", "mcp_server.main"]
