# heron

A small toolkit to triage suspicious emails: parse `.eml` files, extract
phishing indicators (pressure words, links to bare IP addresses or punycode
domains, brand claims and look-alike sender domains, SPF/DMARC failures,
replies sent to another domain) and produce a verdict: benign, suspicious,
or phishing.

> Course project for *Industrial Software Development*. This repository
> evolves throughout the semester; see the tags for each stage.

## Usage

Install heron and the dev tools with uv, then run it from the repository root:

```bash
uv sync                       # create .venv from uv.lock (heron + dev tools)
uv run heron data/samples
```

It prints each verdict with the findings behind it, then a summary. The path
can also be one `.eml` file; `--json` gives machine-readable output, `--help`
lists the options.

Run the tests, with branch coverage and its 85 % gate:

```bash
uv run pytest --cov
```

## Configuration

Settings come from environment variables or from a local `.env` file (copy
`.env.example`; never commit `.env`). They are checked at startup
(`src/heron/config.py`); a bad value stops the program with exit code 2.

| Variable | Default | Meaning |
|---|---|---|
| `HERON_DB` | unset | SQLite file that stores the verdicts (unset = not stored); also `--db` |
| `HERON_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR`; logs are JSON lines on stderr |

## Run in a container

```bash
docker compose build              # build the image from uv.lock
docker compose run --rm triage    # (profile batch) triage the bundled samples; verdicts go to a volume
docker compose run --rm triage    # run it again: the stored verdicts grow from 6 to 12
```

## Run the API

```bash
uv run uvicorn heron.api:app --reload      # http://127.0.0.1:8000/docs
# json.dumps turns the raw message into one valid JSON string
python -c 'import json,sys; print(json.dumps({"raw_eml": open(sys.argv[1]).read()}))' \
  data/samples/prize-scam.eml | curl -s -H 'content-type: application/json' -d @- localhost:8000/triage
```

Storage is injected: endpoints depend on the `VerdictRepository` port
(`src/heron/storage.py`); with `HERON_DB` set they get the SQLite adapter
`VerdictStore`. Errors are RFC 9457 problem details (`application/problem+json`).
In a container: `docker compose up api`; the CLI service is `docker compose run --rm triage`
(profile `batch`).

## Status

Packaged (`pyproject.toml`, src layout, committed `uv.lock`), formatted and
linted (ruff), typed (mypy strict), with a pre-commit hook and an API
reference built from the docstrings by Sphinx
(`uv run sphinx-build -W docs docs/_build`), and tested
with pytest and Hypothesis (unit, integration and property-based tests). CI
(GitHub Actions) checks every pull request, publishes a release for each
version tag and pushes the container image to GHCR. A FastAPI service exposes
the engine over HTTP (ADR 0001 in `docs/adr/`).
