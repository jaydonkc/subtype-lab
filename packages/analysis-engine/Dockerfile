FROM python:3.12-slim

WORKDIR /app
COPY packages/analysis-engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY packages/analysis-engine/analysis_engine /app/analysis_engine
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "analysis_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
