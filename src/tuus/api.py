"""Same-origin synthesis and base-path portable static application."""

import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from starlette.concurrency import run_in_threadpool

from .corpus import ROOT
from .generation import ModelUnavailable
from .prior import Prior
from .runtime import Runtime
from .schema import Record


class SynthesisRequest(Record):
    intent: str = Field(min_length=1, max_length=2000)
    prior: Prior


def create_app(root: Path = ROOT, runtime=None, mounts: tuple[str, ...] | None = None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.runtime = runtime or Runtime(root, os.getenv("TUUS_MODEL_URL", "http://127.0.0.1:8081/v1"))
        yield
        if runtime is None:
            app.state.runtime.model.close()

    app = FastAPI(title="TμUS", docs_url=None, redoc_url=None,
                  openapi_url=None, lifespan=lifespan)
    prefixes = mounts or (os.getenv("TUUS_BASE_PATH", ""),)
    web = root / "web/dist"

    async def synthesize(request: SynthesisRequest):
        intent = request.intent.strip()
        if not intent:
            raise HTTPException(422, "An intent is required.")
        try:
            result = await run_in_threadpool(app.state.runtime.generate,
                                            intent, request.prior, secrets.randbits(32))
        except ModelUnavailable as error:
            raise HTTPException(503, "Synthesis is temporarily unavailable.") from error
        # Retrieval provenance is retained internally rather than exposed in v1 UI.
        return JSONResponse({"utterance": result["utterance"]})

    async def health():
        return {"status": "ready"}

    async def index():
        return FileResponse(web / "index.html")

    async def redirect_to_index(request: Request):
        return RedirectResponse(request.url.path.rstrip("/") + "/")

    for prefix in prefixes:
        if prefix and (not prefix.startswith("/") or prefix.endswith("/")):
            raise ValueError("Base path must be empty or begin with / and have no trailing slash")
        app.add_api_route(prefix + "/api/synthesize", synthesize, methods=["POST"])
        app.add_api_route(prefix + "/api/health", health, methods=["GET"])
        app.add_api_route(prefix + "/", index, methods=["GET"])
        if prefix:
            app.add_api_route(prefix, redirect_to_index, methods=["GET"])
        if web.exists():
            app.mount(prefix + "/assets", StaticFiles(directory=web / "assets"))
    return app


def app_factory():
    return create_app()
