"""Onboarding endpoints — budget setup + sample data seeding."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from supabase import Client

from auth import get_current_user
from database import get_supabase
from models import (
    BudgetRuleCreate,
    RuleType,
    TransactionCreate,
    TransactionType,
    User,
)
from services import budget_rule_service, transaction_service

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# ── Request / response schemas ───────────────────────────────────


class OnboardingStatusResponse(BaseModel):
    needs_onboarding: bool


class OnboardingCompleteRequest(BaseModel):
    monthly_income: float
    budget_strategy: str = "50_30_20"  # "50_30_20" | "80_20" | "custom"
    # Custom percentages (only used when strategy is "custom")
    needs_pct: Optional[float] = None
    wants_pct: Optional[float] = None
    savings_pct: Optional[float] = None


class OnboardingCompleteResponse(BaseModel):
    success: bool
    transactions_created: int
    rules_created: int


# ── Sample transactions (relative to user's income) ─────────────

SAMPLE_EXPENSES = [
    {"pct": 0.27, "description": "Rent Payment", "category": "Housing", "days_ago": 6},
    {"pct": 0.009, "description": "Whole Foods Groceries", "category": "Food & Dining", "days_ago": 5},
    {"pct": 0.0025, "description": "Capital One Cafe", "category": "Food & Dining", "days_ago": 5},
    {"pct": 0.011, "description": "Gas Station - Shell", "category": "Transportation", "days_ago": 4},
    {"pct": 0.003, "description": "Netflix Subscription", "category": "Entertainment", "days_ago": 4},
    {"pct": 0.018, "description": "Amazon - Electronics", "category": "Shopping", "days_ago": 3},
    {"pct": 0.024, "description": "Electric Bill", "category": "Utilities", "days_ago": 3},
    {"pct": 0.013, "description": "Internet - Comcast", "category": "Utilities", "days_ago": 3},
    {"pct": 0.0065, "description": "Uber Ride", "category": "Transportation", "days_ago": 2},
    {"pct": 0.0157, "description": "Dinner - Olive Garden", "category": "Food & Dining", "days_ago": 2},
    {"pct": 0.002, "description": "Spotify Premium", "category": "Entertainment", "days_ago": 1},
    {"pct": 0.0085, "description": "Target - Household Items", "category": "Shopping", "days_ago": 1},
    {"pct": 0.0056, "description": "Chipotle", "category": "Food & Dining", "days_ago": 0},
]


# ── Endpoints ────────────────────────────────────────────────────


@router.get("/status", response_model=OnboardingStatusResponse)
def onboarding_status(
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Check whether the user still needs onboarding."""
    tx = supabase.table("veto_transactions").select("id", count="exact").eq("user_id", user.id).limit(1).execute()
    rules = supabase.table("veto_budget_rules").select("id", count="exact").eq("user_id", user.id).limit(1).execute()

    has_data = bool(tx.data) or bool(rules.data)
    return OnboardingStatusResponse(needs_onboarding=not has_data)


@router.post("/complete", response_model=OnboardingCompleteResponse)
def complete_onboarding(
    body: OnboardingCompleteRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Set up budget rules and seed sample transactions."""
    now = datetime.now(timezone.utc)
    income = body.monthly_income
    tx_count = 0
    rule_count = 0

    # ── 1. Create budget rules based on chosen strategy ──────────
    if body.budget_strategy == "80_20":
        needs_pct, wants_pct, savings_pct = 80, 0, 20
    elif body.budget_strategy == "custom" and body.needs_pct and body.wants_pct and body.savings_pct:
        needs_pct = body.needs_pct
        wants_pct = body.wants_pct
        savings_pct = body.savings_pct
    else:  # default 50/30/20
        needs_pct, wants_pct, savings_pct = 50, 30, 20

    rules_to_create = [
        BudgetRuleCreate(
            rule_type=RuleType.percentage_needs,
            name=f"Needs ≤ {int(needs_pct)}%",
            config=f'{{"percent": {int(needs_pct)}}}',
        ),
        BudgetRuleCreate(
            rule_type=RuleType.percentage_wants,
            name=f"Wants ≤ {int(wants_pct)}%",
            config=f'{{"percent": {int(wants_pct)}}}',
        ),
        BudgetRuleCreate(
            rule_type=RuleType.percentage_allocation,
            name=f"Save ≥ {int(savings_pct)}%",
            config=f'{{"needs": {int(needs_pct)}, "wants": {int(wants_pct)}, "savings": {int(savings_pct)}}}',
        ),
    ]

    for rule_data in rules_to_create:
        budget_rule_service.create_rule(supabase, user.id, rule_data)
        rule_count += 1

    # ── 2. Seed salary income transaction ────────────────────────
    transaction_service.add_transaction(
        supabase,
        user.id,
        TransactionCreate(
            amount=income,
            description="Monthly Salary",
            category="Income",
            transaction_type=TransactionType.income,
            date=now - timedelta(days=6),
        ),
    )
    tx_count += 1

    # Freelance side income (5% of salary)
    transaction_service.add_transaction(
        supabase,
        user.id,
        TransactionCreate(
            amount=round(income * 0.05, 2),
            description="Freelance Payment",
            category="Income",
            transaction_type=TransactionType.income,
            date=now - timedelta(days=2),
        ),
    )
    tx_count += 1

    # ── 3. Seed sample expense transactions ──────────────────────
    for exp in SAMPLE_EXPENSES:
        transaction_service.add_transaction(
            supabase,
            user.id,
            TransactionCreate(
                amount=round(income * exp["pct"], 2),
                description=exp["description"],
                category=exp["category"],
                transaction_type=TransactionType.expense,
                date=now - timedelta(days=exp["days_ago"]),
            ),
        )
        tx_count += 1

    return OnboardingCompleteResponse(
        success=True,
        transactions_created=tx_count,
        rules_created=rule_count,
    )
