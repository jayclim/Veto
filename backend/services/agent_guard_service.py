"""Agent Guard Service — Manages agent spending limits and authorization logging."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional, List

from supabase import Client

from models import (
    _generate_id,
    AgentSettingsCreate,
    AgentSettingsPublic,
    AgentSettingsUpdate,
    AuthorizationLogCreate,
    AuthorizationLogPublic,
    AuthorizationStatus,
)


# ══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════════════

def get_user_id_from_username(supabase: Client, username: str) -> Optional[str]:
    """Look up a user's UUID from their username."""
    result = supabase.table("veto_users").select("id").eq("username", username).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def get_or_create_user_id(supabase: Client, username: str) -> str:
    """Get user's UUID, creating the user if they don't exist."""
    user_id = get_user_id_from_username(supabase, username)
    if user_id:
        return user_id
    
    # Create user
    new_user = {"id": _generate_id(), "username": username}
    result = supabase.table("veto_users").insert(new_user).execute()
    return result.data[0]["id"]

def get_agent_settings(supabase: Client, user_id: str) -> Optional[AgentSettingsPublic]:
    """Get agent settings for a user. Returns None if not configured."""
    result = (
        supabase.table("veto_agent_settings")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    if result.data and len(result.data) > 0:
        return AgentSettingsPublic(**result.data[0])
    return None


def get_or_create_agent_settings(supabase: Client, user_id: str) -> AgentSettingsPublic:
    """Get agent settings for a user, creating defaults if not exists."""
    existing = get_agent_settings(supabase, user_id)
    if existing:
        return existing
    
    # Create default settings
    return create_agent_settings(supabase, user_id, AgentSettingsCreate())


def create_agent_settings(
    supabase: Client,
    user_id: str,
    data: AgentSettingsCreate,
) -> AgentSettingsPublic:
    """Create agent settings for a user."""
    row = {
        "id": _generate_id(),
        "user_id": user_id,
        "single_transaction_limit": data.single_transaction_limit,
        "daily_limit": data.daily_limit,
        "weekly_limit": data.weekly_limit,
        "monthly_limit": data.monthly_limit,
        "require_approval_above": data.require_approval_above,
        "allowed_categories": json.dumps(data.allowed_categories) if data.allowed_categories else None,
        "blocked_categories": json.dumps(data.blocked_categories) if data.blocked_categories else "[]",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("veto_agent_settings").insert(row).execute()
    return AgentSettingsPublic(**result.data[0])


def update_agent_settings(
    supabase: Client,
    user_id: str,
    data: AgentSettingsUpdate,
) -> Optional[AgentSettingsPublic]:
    """Update agent settings for a user."""
    update_data = {"updated_at": datetime.utcnow().isoformat()}
    
    if data.single_transaction_limit is not None:
        update_data["single_transaction_limit"] = data.single_transaction_limit
    if data.daily_limit is not None:
        update_data["daily_limit"] = data.daily_limit
    if data.weekly_limit is not None:
        update_data["weekly_limit"] = data.weekly_limit
    if data.monthly_limit is not None:
        update_data["monthly_limit"] = data.monthly_limit
    if data.require_approval_above is not None:
        update_data["require_approval_above"] = data.require_approval_above
    if data.allowed_categories is not None:
        update_data["allowed_categories"] = json.dumps(data.allowed_categories)
    if data.blocked_categories is not None:
        update_data["blocked_categories"] = json.dumps(data.blocked_categories)
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    
    result = (
        supabase.table("veto_agent_settings")
        .update(update_data)
        .eq("user_id", user_id)
        .execute()
    )
    
    if result.data:
        return AgentSettingsPublic(**result.data[0])
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Authorization Logging
# ══════════════════════════════════════════════════════════════════════════════

def log_authorization(
    supabase: Client,
    user_id: str,
    data: AuthorizationLogCreate,
) -> AuthorizationLogPublic:
    """Log an authorization attempt."""
    row = {
        "id": _generate_id(),
        "user_id": user_id,
        "agent_id": data.agent_id,
        "action_type": data.action_type,
        "amount": data.amount,
        "category": data.category,
        "merchant": data.merchant,
        "description": data.description,
        "status": data.status.value if isinstance(data.status, AuthorizationStatus) else data.status,
        "reason": data.reason,
        "risk_score": data.risk_score,
        "authorization_token": data.authorization_token,
        "was_executed": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("veto_agent_authorization_log").insert(row).execute()
    return AuthorizationLogPublic(**result.data[0])


def get_authorization_history(
    supabase: Client,
    user_id: str,
    limit: int = 50,
    status_filter: Optional[str] = None,
) -> List[AuthorizationLogPublic]:
    """Get authorization history for a user."""
    query = (
        supabase.table("veto_agent_authorization_log")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    
    if status_filter:
        query = query.eq("status", status_filter)
    
    result = query.execute()
    return [AuthorizationLogPublic(**r) for r in result.data]


def mark_authorization_executed(
    supabase: Client,
    authorization_token: str,
) -> bool:
    """Mark an authorization as executed (purchase was completed)."""
    result = (
        supabase.table("veto_agent_authorization_log")
        .update({"was_executed": True})
        .eq("authorization_token", authorization_token)
        .execute()
    )
    return len(result.data) > 0


def get_cumulative_agent_spend(
    supabase: Client,
    user_id: str,
    period: str = "daily",
) -> float:
    """Get cumulative agent spending for a time period."""
    now = datetime.utcnow()
    
    if period == "daily":
        start_time = now - timedelta(days=1)
    elif period == "weekly":
        start_time = now - timedelta(weeks=1)
    elif period == "monthly":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)
    
    result = (
        supabase.table("veto_agent_authorization_log")
        .select("amount")
        .eq("user_id", user_id)
        .eq("status", "APPROVED")
        .eq("was_executed", True)
        .gte("created_at", start_time.isoformat())
        .execute()
    )
    
    return sum(r.get("amount", 0) for r in result.data)
