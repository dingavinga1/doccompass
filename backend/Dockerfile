FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libnss3 \
        libx11-6 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libasound2 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcairo2 \
        libdrm2 \
        libxkbcommon0 \
        libxss1 \
        libxtst6 \
        xvfb \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN uv sync --no-dev

RUN uv run playwright install --with-deps chromium

COPY app ./app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
