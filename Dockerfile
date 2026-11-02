FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HEADLESS=true \
    RUN_EMAIL=false \
    BROWSER=chrome \
    ROBOT_OUTPUT_DIR=/app/output

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium chromium-driver firefox-esr \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md MANIFEST.in ./
COPY src ./src
COPY tests ./tests
COPY config.yaml ./config.yaml
COPY config.json ./config.json

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir ".[test]"

RUN useradd --create-home --shell /bin/bash runner \
    && mkdir -p /app/output \
    && chown -R runner:runner /app
USER runner

CMD ["python", "-m", "src.cli", "--mode", "robot"]
