import zlib
from pathlib import Path
from typing import Any
from urllib.parse import unquote

_size_index = None


class SizeIndex:
    _instance = None

    def __new__(cls, index_path: Path | None = None) -> Any:
        if cls._instance is None:
            if index_path is None:
                raise ValueError("First initialization requires index_path")
            cls._instance = super().__new__(cls)
            cls._instance._init(index_path)
        return cls._instance

    def _init(self, index_path: Path) -> None:
        self.index = self._load_index(index_path)

    def _read_varint(self, data: bytes, i: int) -> tuple[int, int]:
        shift = 0
        result = 0

        while True:
            b = data[i]
            i += 1
            result |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7

        return result, i

    def _load_index(self, path: Path) -> dict[int, int]:
        data = path.read_bytes()

        crc = 0
        i = 0
        index = {}

        while i < len(data):
            delta, i = self._read_varint(data, i)
            size, i = self._read_varint(data, i)

            crc += delta
            index[crc] = size

        return index

    def get_size(self, url: str) -> int | None:
        decoded = unquote(url)
        crc = zlib.crc32(decoded.encode()) & 0xFFFFFFFF
        return self.index.get(crc)


def init_index(index_path: Path) -> None:
    global _size_index
    if _size_index is None:
        _size_index = SizeIndex(index_path)


def get_size(url: str) -> int | None:
    """Get the size from the hash of a file URL."""
    if _size_index is None:
        raise RuntimeError("Index not initialized. Call init_index() first.")
    return _size_index.get_size(url)
