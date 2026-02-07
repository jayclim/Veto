from fastapi import Depends, Header, HTTPException
from supabase import Client

from database import get_supabase
from models import User, _generate_id


def get_current_user(
    x_user_username: str = Header(...),
    supabase: Client = Depends(get_supabase),
) -> User:
    """Find or create a user based on the X-User-Username header."""
    result = supabase.table("veto_users").select("*").eq("username", x_user_username).execute()

    if result.data:
        return User(**result.data[0], is_new=False)

    new_user = {"id": _generate_id(), "username": x_user_username}
    insert_result = supabase.table("veto_users").insert(new_user).execute()
    return User(**insert_result.data[0], is_new=True)
