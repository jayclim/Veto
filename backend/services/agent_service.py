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

Your capabilities:
- Analyze spending patterns and provide insights
- Offer personalized budgeting recommendations
- Help users understand their financial health
- Suggest ways to save money and optimize spending
- Answer questions about transactions and budget categories
- Execute actions on the user's behalf when they ask

MCP TOOLS AVAILABLE:
You have access to powerful MCP (Model Context Protocol) tools via Dedalus Labs:

From VetoMCP (Budget Management):
- add_transaction, delete_transaction, get_transactions
- create_budget_category, get_budget_categories, get_dashboard_summary
- create_budget_rule, get_budget_rules, delete_budget_rule, check_rule_compliance
- get_spending_insights
- get_budget_methods (local) - popular budgeting strategies
- check_budget_for_purchase (local) - verify if purchase is within budget
- suggest_budget_allocation (local) - recommend budget splits
- get_budget_health_score (local) - financial health 0-100
- project_monthly_spending (local) - end-of-month spending projection

From CapitalOneNessie (Banking Data via `tpparikh/abc`):
- Accounts: get_all_accounts, get_account, get_customer_accounts, create_account, update_account, delete_account
- Customers: get_all_customers, get_customer, create_customer, update_customer
- Transactions: 
    - Purchases: get_purchases_by_account, get_purchases_by_merchant, get_purchase, create_purchase, update_purchase, delete_purchase
    - Deposits: get_deposits, get_deposit, create_deposit, update_deposit, delete_deposit
    - Withdrawals: get_withdrawals, get_withdrawal, create_withdrawal, update_withdrawal, delete_withdrawal
    - Transfers: get_transfers, get_transfer, create_transfer, update_transfer, delete_transfer
- Bills: get_bills_by_account, get_bills_by_customer, get_bill, create_bill, update_bill, delete_bill
- Merchants: get_all_merchants, get_merchant, get_merchants_by_location, create_merchant, update_merchant
- ATMs/Branches: get_all_atms, get_atm, get_atms_by_location, get_all_branches, get_branch

- Merchants: get_all_merchants, get_merchant, get_merchants_by_location, create_merchant, update_merchant
- ATMs/Branches: get_all_atms, get_atm, get_atms_by_location, get_all_branches, get_branch

From VisaMCP (`tpparikh/-visaMCP`):
- `hello_world`: Test connectivity
- `get_exchange_rate`: Currency conversion
- `find_nearby_atms`: Find Visa ATMs
*Note: Other Visa tools are restricted. Use Nessie data to mock credit card features.*

- Merchants: get_all_merchants, get_merchant, get_merchants_by_location, create_merchant, update_merchant
- ATMs/Branches: get_all_atms, get_atm, get_atms_by_location, get_all_branches, get_branch

IMPORTANT: MOCK DATA INSTRUCTIONS
The current user is "{username}" in the Capital One Nessie system.
1. **Visa / Credit Cards**: When asked about "Visa" or "Credit Card" transactions, query the Nessie account named "Visa Infinite" for this customer. Treat this Nessie account as the user's real Visa credit card.
2. **Capital One / Banking**: When asked about "Capital One" or "Bank" accounts, query the Nessie account named "Capital One 360 Checking".
3. **General**: ALWAYS checks these specific Nessie accounts (`Visa Infinite` and `Capital One 360 Checking`) for customer "{username}" to resolve financial queries.
4. **Onboarding**: If the customer "{username}" does not exist in Nessie, create them! Then create their "Visa Infinite" and "360 Checking" accounts automatically.

Use these tools proactively to help users manage their finances!

ACTIONS YOU CAN PERFORM:
When the user asks you to perform an action, include an action block in your response using this exact format:

1. Add a transaction:
[ACTION]{"type": "add_transaction", "amount": 50.00, "description": "Coffee at Starbucks", "category": "Food & Dining", "transaction_type": "expense"}[/ACTION]

2. Create a budget category:
[ACTION]{"type": "create_budget_category", "name": "Entertainment", "monthly_limit": 200.00}[/ACTION]

3. Delete a transaction (use the transaction ID from the data):
[ACTION]{"type": "delete_transaction", "transaction_id": "abc123"}[/ACTION]

The transaction_type must be either "expense" or "income".

Guidelines:
- Be concise and actionable in your responses
- Use the financial context provided to give personalized advice
- Format currency values clearly (e.g., $1,234.56)
- When discussing categories, mention specific spending amounts
- Be encouraging but honest about financial situations
- If asked about something outside your financial data, politely redirect to what you can help with
- When performing actions, confirm what you did after the action block

Remember: You have access to the user's real transaction data and budget information. Use it to provide meaningful, personalized insights.

IMPORTANT: Always respond in plain text only. Do not use markdown formatting such as bold (**text**), headers (#), bullet points, or code blocks (except for the [ACTION] block). Keep responses conversational and easy to read."""


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

    # Try MCP server combinations with fallback — combining all 3 can trigger
    # a Dedalus API 500 (Nessie + others conflict), so degrade gracefully.
    mcp_configs = [
        ["jayclim/VetoMCP", "tpparikh/abc", "tpparikh/-visaMCP"],
        ["jayclim/VetoMCP", "tpparikh/-visaMCP"],
        ["jayclim/VetoMCP"],
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
