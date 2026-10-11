"""Pinned local semantic encoder. Corpus encoding is an offline operation."""

from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ort.disable_telemetry_events()


class Encoder:
    def __init__(self, model_dir: Path):
        self.tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(model_dir / "model.onnx"),
                                            options, providers=["CPUExecutionProvider"])

    def _encode(self, texts: list[str]) -> np.ndarray:
        encoded = self.tokenizer.encode_batch(texts)
        ids = np.asarray([item.ids for item in encoded], dtype=np.int64)
        mask = np.asarray([item.attention_mask for item in encoded], dtype=np.int64)
        values = {"input_ids": ids, "attention_mask": mask,
                  "token_type_ids": np.zeros_like(ids)}
        inputs = {item.name: values[item.name] for item in self.session.get_inputs()}
        output = self.session.run(None, inputs)[0]
        expanded = mask[:, :, None]
        pooled = (output * expanded).sum(axis=1) / expanded.sum(axis=1).clip(min=1)
        return (pooled / np.linalg.norm(pooled, axis=1, keepdims=True).clip(min=1e-12)).astype(np.float32)

    def query(self, text: str) -> np.ndarray:
        return self._encode([f"query: {text}"])[0]

    def corpus(self, texts: list[str]) -> np.ndarray:
        return self._encode([f"passage: {text}" for text in texts])
