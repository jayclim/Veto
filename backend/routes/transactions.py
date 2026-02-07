from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from auth import get_current_user
from database import get_supabase
from models import (
    TransactionCreate,
    TransactionPublic,
    TransactionType,
    User,
)
from services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionPublic)
def create_transaction(
    body: TransactionCreate,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return transaction_service.add_transaction(supabase, user.id, body)


@router.get("", response_model=List[TransactionPublic])
def list_transactions(
    category: Optional[str] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return transaction_service.get_transactions(
        supabase, user.id, category, transaction_type, start_date, end_date
    )


@router.delete("/{transaction_id}")
def remove_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    deleted = transaction_service.delete_transaction(supabase, user.id, transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"ok": True}
