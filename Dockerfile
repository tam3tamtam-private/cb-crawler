FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv sync --locked --no-dev

COPY . .

CMD ["uv", "run", "python", "-m", "crawler.main"]
