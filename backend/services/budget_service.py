"""Budget business logic — Supabase-powered standalone functions."""
from __future__ import annotations

from datetime import datetime

from supabase import Client

from models import (
    BudgetCategoryCreate,
    BudgetCategoryPublic,
    CategorySummary,
    DashboardSummary,
    TransactionType,
    _generate_id,
)


def create_category(
    supabase: Client,
    user_id: str,
    data: BudgetCategoryCreate,
) -> BudgetCategoryPublic:
    """Create a budget category for a user."""
    row = {
        "id": _generate_id(),
        "user_id": user_id,
        "name": data.name,
        "monthly_limit": data.monthly_limit,
        "created_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("budget_category").insert(row).execute()
    return BudgetCategoryPublic(**result.data[0])


def get_categories(
    supabase: Client,
    user_id: str,
) -> list[BudgetCategoryPublic]:
    """List all budget categories for a user."""
    result = supabase.table("budget_category").select("*").eq("user_id", user_id).execute()
    return [BudgetCategoryPublic(**r) for r in result.data]


def get_dashboard_summary(
    supabase: Client,
    user_id: str,
) -> DashboardSummary:
    """Build a dashboard summary: totals + per-category breakdown."""
    tx_result = supabase.table("transaction").select("*").eq("user_id", user_id).execute()
    transactions = tx_result.data

    total_income = sum(t["amount"] for t in transactions if t["transaction_type"] == TransactionType.income.value)
    total_expenses = sum(t["amount"] for t in transactions if t["transaction_type"] == TransactionType.expense.value)

    # Per-category spending
    expense_by_cat: dict[str, float] = {}
    for t in transactions:
        if t["transaction_type"] == TransactionType.expense.value:
            expense_by_cat[t["category"]] = expense_by_cat.get(t["category"], 0) + t["amount"]

    # Budget limits lookup
    budget_result = supabase.table("budget_category").select("*").eq("user_id", user_id).execute()
    limit_map = {b["name"]: b["monthly_limit"] for b in budget_result.data}

    categories: list[CategorySummary] = []
    all_cats = set(expense_by_cat.keys()) | set(limit_map.keys())
    for cat in sorted(all_cats):
        spent = expense_by_cat.get(cat, 0)
        limit = limit_map.get(cat)
        categories.append(
            CategorySummary(
                category=cat,
                total_spent=spent,
                budget_limit=limit,
                remaining=limit - spent if limit is not None else None,
            )
        )

    return DashboardSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net=total_income - total_expenses,
        categories=categories,
    )
