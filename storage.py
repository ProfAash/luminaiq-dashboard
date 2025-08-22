# storage.py
from __future__ import annotations
import os
from datetime import datetime
from typing import Optional, Tuple

SUPABASE_URL = os.environ.get("SUPABASE_URL") or ""
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or ""
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "luminaiq-uploads")

_client = None  # type: ignore

def _check_config() -> None:
    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY and SUPABASE_BUCKET):
        raise RuntimeError(
            "Supabase config missing. Set SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET in Streamlit Secrets."
        )

def _import_supabase():
    try:
        from supabase import create_client, Client  # type: ignore
        return create_client, Client
    except Exception as e:
        # Show the true import error
        raise RuntimeError(f"Supabase import failed: {type(e).__name__}: {e}")


def supabase():
    global _client
    if _client is None:
        _check_config()
        create_client, _Client = _import_supabase()
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client

def upload_bytes(filename: str, content: bytes, content_type: str = "text/csv") -> Tuple[str, str]:
    """Upload bytes to Supabase Storage and return (path_in_bucket, public_url)."""
    _check_config()
    _import_supabase()  # ensures clear error if package missing

    day = datetime.utcnow().strftime("%Y-%m-%d")
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe = filename.replace(" ", "_")
    path = f"uploads/{day}/{ts}__{safe}"

    sb = supabase().storage.from_(SUPABASE_BUCKET)
    sb.upload(path, content, {"content-type": content_type, "x-upsert": "true"})
    public_url = sb.get_public_url(path)
    return path, public_url

def create_signed_url(path: str, expires_in: int = 3600) -> str:
    _check_config()
    _import_supabase()
    sb = supabase().storage.from_(SUPABASE_BUCKET)
    res = sb.create_signed_url(path, expires_in=expires_in)
    return res.get("signedURL") or res.get("signedUrl") or ""


