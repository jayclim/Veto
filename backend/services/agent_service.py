"""AI Agent Service — Financial planning and budgeting assistant using Dedalus Labs API."""
from __future__ import annotations

import re
import json
from datetime import datetime
from typing import Optional, Any
from sqlmodel import Session
from dedalus_labs import AsyncDedalus, DedalusRunner

from services.budget_service import get_dashboard_summary, get_categories, create_category
from services.transaction_service import get_transactions, add_transaction, delete_transaction
from models import TransactionCreate, TransactionType, BudgetCategoryCreate

# Dedalus Labs API configuration
DEDALUS_API_KEY = "dsk-live-228425783a32-de8c3254bb7611e7d8c0f463ba26f797"

SYSTEM_PROMPT = """You are Veto AI, a friendly and knowledgeable personal financial advisor integrated into the Veto budgeting app.

Your capabilities:
- Analyze spending patterns and provide insights
- Offer personalized budgeting recommendations
- Help users understand their financial health
- Suggest ways to save money and optimize spending
- Answer questions about transactions and budget categories
- Execute actions on the user's behalf when they ask

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


def _build_financial_context(session: Session, user_id: str) -> str:
    """Build a context string with the user's financial data."""
    # Get dashboard summary
    summary = get_dashboard_summary(session, user_id)
    
    # Get recent transactions (last 20)
    transactions = get_transactions(session, user_id)[:20]
    
    # Get budget categories
    categories = get_categories(session, user_id)
    
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
        # Remove action block from text
        clean_text = re.sub(action_pattern, '', response_text, flags=re.DOTALL).strip()
        return clean_text, action
    except json.JSONDecodeError:
        return response_text, None


def _execute_action(session: Session, user_id: str, action: dict) -> dict[str, Any]:
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
        result = add_transaction(session, user_id, tx_data)
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
        result = create_category(session, user_id, cat_data)
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
        success = delete_transaction(session, user_id, tx_id)
        return {
            "type": "delete_transaction",
            "success": success,
            "details": {"transaction_id": tx_id}
        }
    
    return {"type": action_type, "success": False, "error": "Unknown action type"}


async def generate_response(
    session: Session,
    user_id: str,
    user_message: str,
    conversation_history: Optional[list[dict]] = None,
) -> tuple[str, list[dict]]:
    """Generate an AI response for the user's financial query.
    
    Returns: (response_text, list_of_executed_actions)
    """
    
    # Build financial context
    financial_context = _build_financial_context(session, user_id)
    
    # Build the full prompt with context
    full_prompt = f"""{SYSTEM_PROMPT}

Here is the user's current financial data:

{financial_context}

"""
    
    # Add conversation history context if provided
    if conversation_history:
        full_prompt += "\nRecent conversation:\n"
        for msg in conversation_history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            full_prompt += f"{role}: {content}\n"
        full_prompt += "\n"
    
    full_prompt += f"User: {user_message}\n\nAssistant:"
    
    # Use Dedalus Labs SDK
    client = AsyncDedalus(api_key=DEDALUS_API_KEY)
    runner = DedalusRunner(client)
    
    result = await runner.run(
        model="gpt-5.2",
        input=full_prompt,
    )
    
    # Parse and execute any actions
    response_text, action = _parse_action(result.content)
    executed_actions = []
    
    if action:
        action_result = _execute_action(session, user_id, action)
        executed_actions.append(action_result)
    
    return response_text, executed_actions
