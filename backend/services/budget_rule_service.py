"""Budget rule business logic — Supabase-powered standalone functions."""
from __future__ import annotations

import json
from datetime import datetime

from supabase import Client

from models import (
    BudgetRuleCreate,
    BudgetRulePublic,
    RuleType,
    TransactionType,
    _generate_id,
)


def create_rule(
    supabase: Client,
    user_id: str,
    data: BudgetRuleCreate,
) -> BudgetRulePublic:
    """Create a new budget rule for a user."""
    row = {
        "id": _generate_id(),
        "user_id": user_id,
        "rule_type": data.rule_type.value,
        "name": data.name,
        "config": data.config,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("budget_rule").insert(row).execute()
    return BudgetRulePublic(**result.data[0])


def get_rules(
    supabase: Client,
    user_id: str,
    active_only: bool = True,
) -> list[BudgetRulePublic]:
    """List all budget rules for a user."""
    query = supabase.table("budget_rule").select("*").eq("user_id", user_id)
    if active_only:
        query = query.eq("is_active", True)
    result = query.execute()
    return [BudgetRulePublic(**r) for r in result.data]


def delete_rule(
    supabase: Client,
    user_id: str,
    rule_id: str,
) -> bool:
    """Delete a budget rule. Returns True if deleted."""
    result = (
        supabase.table("budget_rule")
        .delete()
        .eq("id", rule_id)
        .eq("user_id", user_id)
        .execute()
    )
    return len(result.data) > 0


def check_rule_compliance(
    supabase: Client,
    user_id: str,
) -> dict:
    """Check if the user is following their active budget rules."""
    rules_result = (
        supabase.table("budget_rule")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    rules = rules_result.data

    if not rules:
        return {"status": "no_rules", "message": "No active budget rules found."}

    # Get transactions for analysis
    tx_result = supabase.table("transaction").select("*").eq("user_id", user_id).execute()
    transactions = tx_result.data

    total_income = sum(t["amount"] for t in transactions if t["transaction_type"] == TransactionType.income.value)
    total_expenses = sum(t["amount"] for t in transactions if t["transaction_type"] == TransactionType.expense.value)

    # Per-category spending
    expense_by_cat: dict[str, float] = {}
    for t in transactions:
        if t["transaction_type"] == TransactionType.expense.value:
            expense_by_cat[t["category"]] = expense_by_cat.get(t["category"], 0) + t["amount"]

    results = []
    for rule in rules:
        config = json.loads(rule["config"]) if rule["config"] else {}
        rule_type = rule["rule_type"]
        compliance = {"rule_name": rule["name"], "rule_type": rule_type}

        if rule_type == RuleType.percentage_allocation.value:
            if total_income > 0:
                savings_rate = ((total_income - total_expenses) / total_income) * 100
                target_savings = config.get("savings", 20)
                compliance["target_savings_pct"] = target_savings
                compliance["actual_savings_pct"] = round(savings_rate, 1)
                compliance["compliant"] = savings_rate >= target_savings
            else:
                compliance["compliant"] = None
                compliance["message"] = "No income recorded yet."

        elif rule_type == RuleType.category_limit.value:
            category = config.get("category", "")
            limit = config.get("limit", 0)
            spent = expense_by_cat.get(category, 0)
            compliance["category"] = category
            compliance["limit"] = limit
            compliance["spent"] = spent
            compliance["compliant"] = spent <= limit

        elif rule_type == RuleType.savings_goal.value:
            goal = config.get("goal", 0)
            saved = total_income - total_expenses
            compliance["goal"] = goal
            compliance["saved"] = saved
            compliance["compliant"] = saved >= goal

        elif rule_type == RuleType.spending_alert.value:
            category = config.get("category", "")
            threshold = config.get("threshold", 0)
            spent = expense_by_cat.get(category, 0)
            compliance["category"] = category
            compliance["threshold"] = threshold
            compliance["spent"] = spent
            compliance["alert_triggered"] = spent >= threshold
            compliance["compliant"] = spent < threshold

        results.append(compliance)

    return {"status": "checked", "rules": results}
