FROM python:3.12-slim-trixie

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

ENV UV_COMPILE_BYTECODE=1 UV_NO_VAVHE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

# The next two copy commands are written separetely because instead the content of src will be copied to ./
COPY README.md LICENSE ./
COPY src ./src
RUN uv sync --no-dev --frozen
COPY data/samples ./data/samples

# Create a command to swtich user and don't run in root
RUN useradd --create-home app
RUN mkdir -p /data
RUN chown app /data

#####################################################################
# We are in a different layer

USER app
# Now we execute the app by setting the right path
ENV PATH="$PATH:/app/.venv/bin"
ENTRYPOINT ["heron"]
# Now we want to produce default arguments
CMD ["/app/data/samples"]
