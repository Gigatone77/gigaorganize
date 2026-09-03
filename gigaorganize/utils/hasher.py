import hashlib
from pathlib import Path

CHUNK_SIZE = 65536
PARTIAL_SIZE = 16384


def partial_hash(path: Path) -> str:
    h = hashlib.blake2b(digest_size=16)
    with open(path, "rb") as f:
        h.update(f.read(PARTIAL_SIZE))
    return h.hexdigest()


def full_hash(path: Path) -> str:
    h = hashlib.blake2b(digest_size=32)
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()
