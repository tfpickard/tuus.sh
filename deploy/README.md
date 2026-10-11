# Portable service deployment

The application consists of static browser assets, a Python HTTP service, and a
local small-model HTTP service. Caddy supplies TLS. A Linux VPS with sufficient
memory for the model and encoder is the proposed deployment environment.

Prepare the immutable artifacts before deployment:

```sh
uv sync
uv run python scripts/fetch_models.py
uv run tuus validate
uv run tuus build
```

Point the canonical domain's DNS at the selected host, then run:

```sh
docker compose -f deploy/compose.yaml up --build -d
```

For another origin set `TUUS_DOMAIN`. For a mirror under a path set
`TUUS_BASE_PATH=/tuus` and route that prefix to the API service while preserving
the request path. The identical frontend build resolves assets and synthesis
relative to its document location. The mirror host's existing proxy can replace
Caddy without application changes.

Only the proxy exposes public ports. Model weights are mounted read-only, and no
user inputs are persisted. The inference endpoint is private to the service network.
Container images are pinned to inspected manifest digests. The model and encoder
files have a checked, revision-pinned manifest. Updating either requires renewed
verification.

Serving the Python process through systemd and running an independently installed
`llama-server` is also supported; containers are a packaging option.
