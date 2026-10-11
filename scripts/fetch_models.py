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
    expected = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest = {}
    for relative, url in FILES.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o755)
        if not path.exists():
            print(f"Fetching {relative}", flush=True)
            temporary = path.with_suffix(path.suffix + ".partial")
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as out:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    out.write(block)
            temporary.replace(path)
        checksum = sha256(path)
        path.chmod(0o644)
        if relative in expected and expected[relative]["sha256"] != checksum:
            raise ValueError(f"Model checksum mismatch: {relative}")
        manifest[relative] = {"url": url, "sha256": checksum, "bytes": path.stat().st_size}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Verified {relative}: {path.stat().st_size} bytes", flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
