"""AI Agent Service — Financial planning and budgeting assistant using Dedalus Labs API."""
from __future__ import annotations

import os
import re
import json
from datetime import datetime
from typing import Optional, Any
from supabase import Client
from dedalus_labs import AsyncDedalus, DedalusRunner

from services.budget_service import get_dashboard_summary, get_categories, create_category
from services.transaction_service import get_transactions, add_transaction, delete_transaction
from models import TransactionCreate, TransactionType, BudgetCategoryCreate
from database import SUPABASE_URL  # triggers dotenv loading

# Dedalus Labs API configuration
DEDALUS_API_KEY = os.environ.get("DEDALUS_API_KEY", "")

SYSTEM_PROMPT = """You are Veto AI, a friendly and knowledgeable personal financial advisor integrated into the Veto budgeting app.

CRITICAL: You have MCP tools available. You MUST call them to fulfill user requests. NEVER say a tool is "unavailable" — just call it. Always pass username="{username}" to every tool call.

YOUR MCP TOOLS:

WRITE TOOLS (VetoMCP — for creating, updating, or deleting data):
- add_transaction(amount, description, category, transaction_type, username) — record expense or income
- delete_transaction(transaction_id, username) — remove a transaction
- create_budget_category(name, monthly_limit, username) — create a category
- create_budget_rule(rule_type, name, config, username) — create a budget rule
- delete_budget_rule(rule_id, username) — delete a budget rule
- get_budget_rules(username) — list rules (call first to get IDs before deleting)

READ TOOLS (VetoMCP):
- get_transactions(username) — list transactions
- get_budget_categories(username) — list categories
- get_dashboard_summary(username) — financial overview
- check_rule_compliance(username) — check rule compliance
- get_spending_insights(username) — spending analysis
- get_budget_methods() — popular budgeting strategies
- suggest_budget_allocation(monthly_income, method) — recommend splits
- get_budget_health_score(total_income, total_expenses, ...) — 0-100 health score

READ-ONLY TOOLS (CapitalOneNessie via tpparikh/abc):
- get_all_accounts, get_account, get_customer_accounts
- get_all_customers, get_customer
- get_purchases_by_account, get_purchases_by_merchant, get_purchase
- get_deposits, get_deposit, get_withdrawals, get_withdrawal
- get_transfers, get_transfer
- get_bills_by_account, get_bills_by_customer, get_bill
- get_all_merchants, get_merchant, get_merchants_by_location
- get_all_atms, get_atm, get_all_branches, get_branch

READ-ONLY TOOLS (VisaMCP via tpparikh/-visaMCP):
- get_exchange_rate — currency conversion
- find_nearby_atms — find Visa ATMs

MOCK DATA INSTRUCTIONS:
The current user is "{username}" in the Capital One Nessie system.
1. For "Visa" or "Credit Card" queries, use the Nessie account named "Visa Infinite" for customer "{username}".
2. For "Capital One" or "Bank" queries, use the Nessie account named "Capital One 360 Checking".
3. If customer "{username}" does not exist in Nessie, create them with "Visa Infinite" and "360 Checking" accounts.

WORKFLOW FOR MULTI-STEP OPERATIONS:
- To delete all budget rules: first call get_budget_rules(username="{username}") to get IDs, then call delete_budget_rule for each.
- To replace rules: delete existing ones first, then create new ones.

Guidelines:
- Be concise and actionable
- Format currency values clearly (e.g., $1,234.56)
- Be encouraging but honest about financial situations
- When performing actions, confirm what you did
- Always respond in plain text only. No markdown formatting (no bold, headers, bullets, code blocks)."""


def _build_financial_context(supabase: Client, user_id: str) -> str:
    """Build a context string with the user's financial data."""
    summary = get_dashboard_summary(supabase, user_id)
    transactions = get_transactions(supabase, user_id)[:20]
    categories = get_categories(supabase, user_id)

    context_parts = [
        "## Current Financial Overview",
        f"- Total Income: ${summary.total_income:,.2f}",
        f"- Total Expenses: ${summary.total_expenses:,.2f}",
        f"- Net Balance: ${summary.net:,.2f}",
        "",
        "## Spending by Category"
    ]

    for cat in summary.categories:
        if cat.budget_limit:
            status = "under" if (cat.remaining or 0) > 0 else "over"
            context_parts.append(
                f"- {cat.category}: ${cat.total_spent:,.2f} spent "
                f"(budget: ${cat.budget_limit:,.2f}, {status} by ${abs(cat.remaining or 0):,.2f})"
            )
        else:
            context_parts.append(f"- {cat.category}: ${cat.total_spent:,.2f} spent (no budget set)")

    if transactions:
        context_parts.extend(["", "## Recent Transactions (last 20)"])
        for tx in transactions:
            tx_type = "+" if tx.transaction_type.value == "income" else "-"
            context_parts.append(
                f"- ID: {tx.id} | {tx_type}${tx.amount:,.2f} | {tx.category} | {tx.description} | {tx.date.strftime('%Y-%m-%d')}"
            )

    if categories:
        context_parts.extend(["", "## Budget Categories"])
        for cat in categories:
            context_parts.append(f"- {cat.name}: ${cat.monthly_limit:,.2f}/month")

    return "\n".join(context_parts)


def _parse_action(response_text: str) -> tuple[str, Optional[dict]]:
    """Parse action block from response. Returns (clean_text, action_dict or None)."""
    action_pattern = r'\[ACTION\](.*?)\[/ACTION\]'
    match = re.search(action_pattern, response_text, re.DOTALL)

    if not match:
        return response_text, None

    try:
        action_json = match.group(1).strip()
        action = json.loads(action_json)
        clean_text = re.sub(action_pattern, '', response_text, flags=re.DOTALL).strip()
        return clean_text, action
    except json.JSONDecodeError:
        return response_text, None


def _execute_action(supabase: Client, user_id: str, action: dict) -> dict[str, Any]:
    """Execute an action and return the result."""
    action_type = action.get("type")

    if action_type == "add_transaction":
        tx_type_str = action.get("transaction_type", "expense")
        tx_type = TransactionType.income if tx_type_str == "income" else TransactionType.expense

        tx_data = TransactionCreate(
            amount=float(action.get("amount", 0)),
            description=action.get("description", ""),
            category=action.get("category", "Other"),
            transaction_type=tx_type,
            date=datetime.utcnow(),
        )
        result = add_transaction(supabase, user_id, tx_data)
        return {
            "type": "add_transaction",
            "success": True,
            "details": {
                "id": result.id,
                "amount": result.amount,
                "description": result.description,
                "category": result.category,
            }
        }

    elif action_type == "create_budget_category":
        cat_data = BudgetCategoryCreate(
            name=action.get("name", ""),
            monthly_limit=float(action.get("monthly_limit", 0)),
        )
        result = create_category(supabase, user_id, cat_data)
        return {
            "type": "create_budget_category",
            "success": True,
            "details": {
                "id": result.id,
                "name": result.name,
                "monthly_limit": result.monthly_limit,
            }
        }

    elif action_type == "delete_transaction":
        tx_id = action.get("transaction_id", "")
        success = delete_transaction(supabase, user_id, tx_id)
        return {
            "type": "delete_transaction",
            "success": success,
            "details": {"transaction_id": tx_id}
        }

    return {"type": action_type, "success": False, "error": "Unknown action type"}


async def generate_response(
    supabase: Client,
    user_id: str,
    user_message: str,
    conversation_history: Optional[list[dict]] = None,
) -> tuple[str, list[dict]]:
    """Generate an AI response for the user's financial query.

    Returns: (response_text, list_of_executed_actions)
    """
    financial_context = _build_financial_context(supabase, user_id)

    full_prompt = f"""{SYSTEM_PROMPT.replace("{username}", user_id)}
 
 Here is the user's current financial data:
 
 {financial_context}
 
 """

    if conversation_history:
        full_prompt += "\nRecent conversation:\n"
        for msg in conversation_history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            full_prompt += f"{role}: {content}\n"
        full_prompt += "\n"

    full_prompt += f"User: {user_message}\n\nAssistant:"

    client = AsyncDedalus(api_key=DEDALUS_API_KEY)
    runner = DedalusRunner(client)

    # Try MCP server combinations with fallback.
    # VetoMCP handles writes + budget reads, Nessie/Visa for banking data reads.
    mcp_configs = [
        ["jclim/VetoMCP", "tpparikh/abc", "tpparikh/-visaMCP"],
        ["jclim/VetoMCP", "tpparikh/-visaMCP"],
        ["jclim/VetoMCP"],
        ["tpparikh/abc", "tpparikh/-visaMCP"],
        [],
    ]

    result = None
    for servers in mcp_configs:
        try:
            result = await runner.run(
                model="gpt-5.2",
                input=full_prompt,
                mcp_servers=servers,
            )
            break
        except Exception as e:
            print(f"[AGENT] MCP servers {servers} failed: {e}, trying fallback...")
            continue

    if result is None:
        raise RuntimeError("All MCP server configurations failed")

    response_text, action = _parse_action(result.content)
    executed_actions = []

    if action:
        action_result = _execute_action(supabase, user_id, action)
        executed_actions.append(action_result)

    return response_text, executed_actions
