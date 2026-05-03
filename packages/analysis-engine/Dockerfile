FROM node:22-slim AS web-build

WORKDIR /web
COPY apps/web/package*.json /web/
RUN npm ci
COPY apps/web /web
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
COPY packages/analysis-engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY packages/analysis-engine/analysis_engine /app/analysis_engine
COPY --from=web-build /web/dist /app/static
ENV PYTHONPATH=/app
ENV WEB_DIST_DIR=/app/static
ENV ARTIFACT_ROOT=/app/artifacts
EXPOSE 8000
CMD ["sh", "-c", "uvicorn analysis_engine.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
