FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.27 /uv /uvx /bin/

ENV UV_NO_CACHE=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN uv sync \
    --locked \
    --no-dev \
    --no-install-project \
    --no-editable


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd --system kuma \
    && useradd --system --gid kuma --create-home kuma \
    && mkdir -p /app/reports/models \
    && chown -R kuma:kuma /app/reports

COPY --from=builder --chown=kuma:kuma /app/.venv /app/.venv
COPY --chown=kuma:kuma src ./src

USER kuma

CMD ["python", "-m", "src.security_detector"]