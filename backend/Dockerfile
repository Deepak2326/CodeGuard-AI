FROM python:3.14-slim
WORKDIR /app
COPY backend/requirements.lock /app/backend/requirements.lock
RUN pip install --no-cache-dir -r backend/requirements.lock
COPY backend /app/backend
COPY ml /app/ml
RUN useradd --create-home codeguard && mkdir -p /app/data && chown codeguard:codeguard /app/data
USER codeguard
ENV MODEL_DIR=/app/ml/artifacts
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s CMD python -c "import urllib.request,json; r=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health')); assert r['model_ready']"
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
