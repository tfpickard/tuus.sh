# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS frontend
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca npm ci; else npm ci; fi
COPY web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS runtime
WORKDIR /app
ENV TUUS_ROOT=/app PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md LICENSE ./
COPY deploy/requirements.txt ./requirements.txt
COPY src/ src/
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --no-deps . \
    && useradd --uid 10001 --create-home tuus
COPY corpus/ corpus/
COPY artifacts/ artifacts/
COPY prompts/ prompts/
COPY --from=frontend /app/web/dist/ web/dist/
RUN chmod -R a+rX /app
USER tuus
EXPOSE 8000
CMD ["uvicorn", "tuus.api:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000"]
