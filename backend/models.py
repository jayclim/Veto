from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


def _generate_id() -> str:
    return uuid4().hex


def _camel_alias(field_name: str) -> str:
    parts = field_name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_camel_alias,
        populate_by_name=True,
    )


# ── Enums ────────────────────────────────────────────────────────


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class RuleType(str, Enum):
    percentage_allocation = "percentage_allocation"
    category_limit = "category_limit"
    savings_goal = "savings_goal"
    spending_alert = "spending_alert"


# ── User Model ───────────────────────────────────────────────────


class User(BaseModel):
    id: str
    username: str
    created_at: datetime


# ── Public Models (Pydantic schemas for API) ─────────────────────


class TransactionCreate(CamelModel):
    amount: float
    description: str
    category: str = "Uncategorized"
    transaction_type: TransactionType = TransactionType.expense
    date: Optional[datetime] = None


class TransactionPublic(CamelModel):
    id: str
    amount: float
    description: str
    category: str
    transaction_type: TransactionType
    date: datetime
    created_at: datetime


class BudgetCategoryCreate(CamelModel):
    name: str
    monthly_limit: float


class BudgetCategoryPublic(CamelModel):
    id: str
    name: str
    monthly_limit: float
    created_at: datetime


class CategorySummary(CamelModel):
    category: str
    total_spent: float
    budget_limit: Optional[float] = None
    remaining: Optional[float] = None


class DashboardSummary(CamelModel):
    total_income: float
    total_expenses: float
    net: float
    categories: List[CategorySummary]


class UserPublic(CamelModel):
    id: str
    username: str
    created_at: datetime


class BudgetRuleCreate(CamelModel):
    rule_type: RuleType
    name: str
    config: str  # JSON string


class BudgetRulePublic(CamelModel):
    id: str
    rule_type: RuleType
    name: str
    config: str
    is_active: bool
    created_at: datetime
