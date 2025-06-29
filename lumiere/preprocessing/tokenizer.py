from pathlib import Path
from typing import Iterable

import tokenizers
from datasets import Dataset
from tokenizers import decoders, models, normalizers, pre_tokenizers, trainers


class Tokenizer:
    def __init__(self):
        self.tokenizer = tokenizers.Tokenizer(models.BPE())
        self.tokenizer.normalizer = normalizers.NFKC()
        self.tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel()
        self.tokenizer.decoder = decoders.ByteLevel()

    def train(
        self, dataset: Dataset, text_column: str, batch_size: int, vocab_size: int
    ):
        # If we're trying to not tie the implementation to a specific dataset
        # how do we communicate which column the text is in?
        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError("Batch size must be an integer greater than zero")

        def _train_iter():
            for batch in dataset.select_columns(text_column).iter(batch_size):
                yield batch[text_column]

        trainer = trainers.BpeTrainer(vocab_size=vocab_size, min_frequency=2)
        self.tokenizer.train_from_iterator(_train_iter(), trainer, length=len(dataset))
        return self

    def encode(self, text: str):
        return self.tokenizer.encode(text)

    def decode(self, token_ids: Iterable[str]) -> str:
        return self.tokenizer.decode(token_ids)

    @property
    def vocab_size(self) -> int:
        return self.tokenizer.get_vocab_size()

    def save(self, path: str):
        self.tokenizer.save(path)

    @staticmethod
    def load(path: Path):
        tokenizer = Tokenizer()
        tokenizer.tokenizer = tokenizers.Tokenizer.from_file(str(path))
        return tokenizer

    @staticmethod
    def from_bytes(bytes: bytes):
        tokenizer = Tokenizer()
        tokenizer.tokenizer = tokenizers.Tokenizer.from_str(bytes.decode("utf-8"))
        return tokenizer
