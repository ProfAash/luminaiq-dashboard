# storage.py
import os
from datetime import datetime
from typing import Tuple, Optional

from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "luminaiq-uploads")

_client: Optional[Client] = None

def _client_ok() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY and SUPABASE_BUCKET)

def supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client

def upload_bytes(filename: str, content: bytes, content_type: str = "text/csv") -> Tuple[str, str]:
    """
    Uploads bytes to Supabase Storage and returns (path_in_bucket, public_url)
    """
    if not _client_ok():
        raise RuntimeError("Supabase secrets missing")

    # Path like: uploads/2024-08-21/20240821T120102Z__filename.csv
    day = datetime.utcnow().strftime("%Y-%m-%d")
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_name = filename.replace(" ", "_")
    path = f"uploads/{day}/{ts}__{safe_name}"

    sb = supabase().storage.from_(SUPABASE_BUCKET)

    # If the object already exists, set upsert=True
    sb.upload(path, content, {"content-type": content_type, "x-upsert": "true"})
    public_url = sb.get_public_url(path)
    return path, public_url
