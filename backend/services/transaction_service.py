"""Transaction business logic — Supabase-powered standalone functions."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from supabase import Client

from models import (
    TransactionCreate,
    TransactionPublic,
    TransactionType,
    _generate_id,
)


def add_transaction(
    supabase: Client,
    user_id: str,
    data: TransactionCreate,
) -> TransactionPublic:
    """Create a new transaction for a user."""
    row = {
        "id": _generate_id(),
        "user_id": user_id,
        "amount": data.amount,
        "description": data.description,
        "category": data.category,
        "transaction_type": data.transaction_type.value,
        "date": (data.date or datetime.utcnow()).isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("transaction").insert(row).execute()
    return TransactionPublic(**result.data[0])


def delete_transaction(
    supabase: Client,
    user_id: str,
    transaction_id: str,
) -> bool:
    """Delete a transaction owned by the user. Returns True if deleted."""
    result = (
        supabase.table("transaction")
        .delete()
        .eq("id", transaction_id)
        .eq("user_id", user_id)
        .execute()
    )
    return len(result.data) > 0


def get_transactions(
    supabase: Client,
    user_id: str,
    category: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[TransactionPublic]:
    """Retrieve transactions for a user with optional filters."""
    query = supabase.table("transaction").select("*").eq("user_id", user_id)

    if category:
        query = query.eq("category", category)
    if transaction_type:
        query = query.eq("transaction_type", transaction_type.value)
    if start_date:
        query = query.gte("date", start_date.isoformat())
    if end_date:
        query = query.lte("date", end_date.isoformat())

    result = query.order("date", desc=True).execute()
    return [TransactionPublic(**r) for r in result.data]
