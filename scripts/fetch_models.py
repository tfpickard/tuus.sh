"""Fetch pinned model artifacts; never invoked by the request path."""

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "models/e5-small-v2/model.onnx": "https://huggingface.co/Xenova/e5-small-v2/resolve/02af79985278377e65c724a76275707cb0333c70/onnx/model_quantized.onnx",
    "models/e5-small-v2/tokenizer.json": "https://huggingface.co/Xenova/e5-small-v2/resolve/02af79985278377e65c724a76275707cb0333c70/tokenizer.json",
    "models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf": "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    manifest_path = ROOT / "artifacts/models.json"
    expected = json.loads(manifest_path.read_text())
    if set(expected) != set(FILES):
        raise ValueError("Pinned model manifest does not match the declared artifacts")
    for relative, url in FILES.items():
        if expected[relative]["url"] != url:
            raise ValueError(f"Model revision differs from pinned manifest: {relative}")
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o755)
        if not path.exists():
            print(f"Fetching {relative}", flush=True)
            temporary = path.with_suffix(path.suffix + ".partial")
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as out:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    out.write(block)
            if sha256(temporary) != expected[relative]["sha256"]:
                raise ValueError(f"Downloaded model checksum mismatch: {relative}")
            temporary.replace(path)
        checksum = sha256(path)
        path.chmod(0o644)
        if expected[relative]["sha256"] != checksum or expected[relative]["bytes"] != path.stat().st_size:
            raise ValueError(f"Model checksum mismatch: {relative}")
        print(f"Verified {relative}: {path.stat().st_size} bytes", flush=True)


if __name__ == "__main__":
    main()
