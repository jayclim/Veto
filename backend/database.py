import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

def get_supabase() -> Client:
    """Return a fresh Supabase client to avoid stale HTTP/2 connections."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)
