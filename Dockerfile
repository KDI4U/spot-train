# Dockerfile for railway_api (FastAPI + Selenium/Chromium for the NTES schedule scraper).
# Build from the repo root: docker build -f Dockerfile .
FROM python:3.11-slim

LABEL maintainer="UISPL"
LABEL application="railway-api"
LABEL version="1.0.0"

# Chromium + its matching driver are required by enquiry_train_service.py (Selenium-based NTES
# train-schedule scraper). The requests-based PNR/spot-train lookups don't need a browser, but
# both run in the same process, so the image always carries Chromium.
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        fonts-liberation \
        wget \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY train_status train_status

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8000/ || exit 1

# WEB_CONCURRENCY controls uvicorn worker count (Azure App Settings, docker run -e, etc.) --
# defaults to 1 since Selenium's headless Chrome is memory-heavy per worker.
ENV WEB_CONCURRENCY="1"

ENTRYPOINT ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY}"]
