# syntax=docker/dockerfile:1
FROM python:3.12-slim

# uv from its official image (pinned version); no pip needed
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_NO_CACHE=1
WORKDIR /app

# 1) the dependencies only: this layer is rebuilt only when pyproject.toml or uv.lock change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra api --no-install-project

# 2) the project itself, which changes more often
COPY README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev --extra api
COPY data/samples ./data/samples

# 3) drop root: a user that owns only the data folder, where the verdicts go
RUN useradd --create-home app && mkdir -p /data && chown app /data
USER app

ENV PATH="/app/.venv/bin:$PATH" HERON_DB=/data/verdicts.db
ENTRYPOINT ["heron"]
CMD ["/app/data/samples"]
