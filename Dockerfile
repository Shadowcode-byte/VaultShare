FROM node:22-bookworm-slim AS frontend-build
WORKDIR /work/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ENV=production
WORKDIR /app/backend
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /work/frontend/dist /app/frontend/dist
COPY deployment/start.sh /app/start.sh
RUN chmod +x /app/start.sh && useradd --create-home vault && chown -R vault:vault /app
USER vault
CMD ["/app/start.sh"]
