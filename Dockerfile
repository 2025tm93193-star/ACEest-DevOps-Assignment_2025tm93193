FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ACEEST_DB_PATH=/app/instance/aceest.sqlite3

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY aceest ./aceest
COPY app.py .
COPY tests ./tests
COPY instructor_versions ./instructor_versions

RUN groupadd -r aceest && useradd -r -g aceest aceest \
    && mkdir -p /app/instance \
    && chown -R aceest:aceest /app
USER aceest

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "app:app"]
