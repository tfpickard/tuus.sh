"""Serve the identical frontend bundle at root and a subpath for verification."""

import os

import uvicorn

from tuus.api import create_app

if __name__ == "__main__":
    uvicorn.run(create_app(mounts=("", "/tuus")), host="127.0.0.1",
                port=int(os.environ.get("TUUS_PREVIEW_PORT", "8000")))
