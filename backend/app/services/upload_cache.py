import time
import uuid
from dataclasses import dataclass

_TTL_SECONDS = 15 * 60


@dataclass
class CachedUpload:
    dataset_id: str
    filename: str
    raw: bytes
    created_at: float


_store: dict[str, CachedUpload] = {}


def _purge_expired() -> None:
    now = time.time()
    expired = [token for token, item in _store.items() if now - item.created_at > _TTL_SECONDS]
    for token in expired:
        _store.pop(token, None)


def put(dataset_id: str, filename: str, raw: bytes) -> str:
    _purge_expired()
    token = uuid.uuid4().hex
    _store[token] = CachedUpload(dataset_id=dataset_id, filename=filename, raw=raw, created_at=time.time())
    return token


def pop(token: str) -> CachedUpload | None:
    _purge_expired()
    return _store.pop(token, None)
