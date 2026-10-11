"""Retrieve the pinned Linux x64 inference binary for local operation."""

import hashlib
import tarfile
import urllib.request
from pathlib import Path

URL = "https://github.com/ggml-org/llama.cpp/releases/download/b11552/llama-b11552-bin-ubuntu-x64.tar.gz"
CHECKSUM = "a45a6afda05d08028bd37998072ab602c96799bccde126835941623cb99bb727"
ROOT = Path(__file__).resolve().parents[1]


def main():
    directory = ROOT / "models/llama"
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / "llama.tar.gz"
    if not archive.exists():
        with urllib.request.urlopen(URL, timeout=120) as response, archive.open("wb") as output:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                output.write(block)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != CHECKSUM:
        raise ValueError("Inference binary checksum mismatch")
    with tarfile.open(archive) as handle:
        handle.extractall(directory, filter="data")
    print(directory / "llama-b11552/llama-server")


if __name__ == "__main__":
    main()
