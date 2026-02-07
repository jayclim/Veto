from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from supabase import Client

from auth import get_current_user
from database import get_supabase
from models import (
    BudgetRuleCreate,
    BudgetRulePublic,
    BudgetCompliance,
    User,
)
from services import budget_rule_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("/rules", response_model=BudgetRulePublic)
def create_rule(
    body: BudgetRuleCreate,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return budget_rule_service.create_rule(supabase, user.id, body)


@router.get("/rules", response_model=List[BudgetRulePublic])
def list_rules(
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return budget_rule_service.get_rules(supabase, user.id)


@router.get("/compliance", response_model=BudgetCompliance)
def check_compliance(
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    return budget_rule_service.check_rule_compliance(supabase, user.id)
