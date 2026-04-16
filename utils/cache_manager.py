"""
cache_manager.py — Simple local cache for API responses to reduce API calls
and enable offline functionality for previously queried variants.
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Any


CACHE_DIR = Path(__file__).parent.parent / "data" / ".cache"
CACHE_TTL = 86400 * 7  # 7 days in seconds


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(namespace: str, query: str) -> str:
    """Generate a deterministic cache key."""
    raw = f"{namespace}:{query}".lower().strip()
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cached(namespace: str, query: str) -> Optional[Any]:
    """
    Retrieve a cached result if it exists and hasn't expired.

    Args:
        namespace: Cache namespace (e.g., 'clinvar', 'uniprot')
        query: The query string that was used

    Returns:
        Cached data or None if not found/expired
    """
    _ensure_cache_dir()
    key = _cache_key(namespace, query)
    cache_file = CACHE_DIR / f"{namespace}_{key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if time.time() - data.get("timestamp", 0) > CACHE_TTL:
            cache_file.unlink(missing_ok=True)
            return None
        return data.get("payload")
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def set_cached(namespace: str, query: str, payload: Any):
    """
    Store a result in the cache.

    Args:
        namespace: Cache namespace (e.g., 'clinvar', 'uniprot')
        query: The query string
        payload: Data to cache (must be JSON-serializable)
    """
    _ensure_cache_dir()
    key = _cache_key(namespace, query)
    cache_file = CACHE_DIR / f"{namespace}_{key}.json"

    data = {
        "namespace": namespace,
        "query": query,
        "timestamp": time.time(),
        "payload": payload
    }

    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    except OSError:
        pass  # Silently fail on cache write errors


def clear_cache(namespace: Optional[str] = None):
    """Clear cache entries, optionally filtered by namespace."""
    _ensure_cache_dir()
    pattern = f"{namespace}_*.json" if namespace else "*.json"
    for f in CACHE_DIR.glob(pattern):
        f.unlink(missing_ok=True)
