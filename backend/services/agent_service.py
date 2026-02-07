"""AI Agent Service — Financial planning and budgeting assistant using Dedalus Labs API."""
from __future__ import annotations

import os
import re
import json
from datetime import datetime
from typing import Optional, Any, AsyncGenerator
from supabase import Client
from dedalus_labs import AsyncDedalus, DedalusRunner

from services.budget_rule_service import check_rule_compliance, get_rules, create_rule
from services.transaction_service import get_transactions, add_transaction, delete_transaction
from models import TransactionCreate, TransactionType, BudgetRuleCreate, RuleType
from database import SUPABASE_URL  # triggers dotenv loading

# Dedalus Labs API configuration
DEDALUS_API_KEY = os.environ.get("DEDALUS_API_KEY", "")

SYSTEM_PROMPT = """You are Veto AI, a friendly and knowledgeable personal financial advisor integrated into the Veto budgeting app.

You have MCP tools available. You MUST call them to fulfill user requests. NEVER say a tool is "unavailable" — just call it. Always pass username="{username}" to every tool call.

TERMINOLOGY:
Users may say "budget policy", "budget category", "budget limit", or "budget rule" — these all mean the same thing: a budget rule. Always use the budget rule tools regardless of how the user phrases it.

MOCK DATA:
The current user is "{username}" in the Capital One Nessie system.
- For "Visa" or "Credit Card" queries, use the Nessie account named "Visa Infinite" for customer "{username}".
- For "Capital One" or "Bank" queries, use the Nessie account named "Capital One 360 Checking".

WORKFLOWS:
- To delete all budget rules: first call get_budget_rules to get IDs, then call delete_budget_rule for each.
- To replace rules: delete existing ones first, then create new ones.

Guidelines:
- Be concise and actionable
- Format currency values clearly (e.g., $1,234.56)
- Be encouraging but honest about financial situations
- When performing actions, confirm what you did
- Always respond in plain text only. No markdown formatting (no bold, headers, bullets, code blocks)."""


def _build_financial_context(supabase: Client, user_id: str) -> str:
    """Build a context string with the user's financial data."""
    compliance = check_rule_compliance(supabase, user_id)
    transactions = get_transactions(supabase, user_id)[:20]

    context_parts = [
        "## Current Financial Overview",
        f"- Total Income: ${compliance['total_income']:,.2f}",
        f"- Total Expenses: ${compliance['total_expenses']:,.2f}",
        f"- Net Balance: ${compliance['net']:,.2f}",
        "",
        "## Budget Rules Status"
    ]

    for rule in compliance.get("rules", []):
         status = "COMPLIANT" if rule.get("compliant") else "AT RISK"
         details = ""
         if rule.get("rule_type") == "category_limit":
             details = f"(${rule.get('spent')} / ${rule.get('limit')})"
         elif rule.get("rule_type") == "savings_goal":
             details = f"(Saved: ${rule.get('saved')} / Goal: ${rule.get('goal')})"
         
         context_parts.append(f"- {rule.get('rule_name')}: {status} {details}")

    if transactions:
        context_parts.extend(["", "## Recent Transactions (last 20)"])
        for tx in transactions:
            tx_type = "+" if tx.transaction_type.value == "income" else "-"
            context_parts.append(
                f"- ID: {tx.id} | {tx_type}${tx.amount:,.2f} | {tx.category} | {tx.description} | {tx.date.strftime('%Y-%m-%d')}"
            )

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

    elif action_type == "create_budget_rule":
        try:
            rule_type_enum = RuleType(action.get("rule_type", ""))
        except ValueError:
            return {"type": "create_budget_rule", "success": False, "error": "Invalid rule type"}

        rule_data = BudgetRuleCreate(
            rule_type=rule_type_enum,
            name=action.get("name", ""),
            config=json.dumps(action.get("config", {})),
        )
        result = create_rule(supabase, user_id, rule_data)
        return {
            "type": "create_budget_rule",
            "success": True,
            "details": {
                "id": result.id,
                "name": result.name,
                "rule_type": result.rule_type.value,
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
    username: str,
    user_message: str,
    conversation_history: Optional[list[dict]] = None,
) -> tuple[str, list[dict]]:
    """Generate an AI response for the user's financial query.

    Returns: (response_text, list_of_executed_actions)
    """
    financial_context = _build_financial_context(supabase, user_id)

    full_prompt = f"""{SYSTEM_PROMPT.replace("{username}", username)}
 
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
        # ["jclim/VetoMCP", "tpparikh/-visaMCP"],
        # ["jclim/VetoMCP"],
        # ["tpparikh/abc", "tpparikh/-visaMCP"],
        [],
    ]

    result = None
    for servers in mcp_configs:
        try:
            result = await runner.run(
                model="gemini-2.5-flash",
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


async def generate_response_stream(
    supabase: Client,
    user_id: str,
    username: str,
    user_message: str,
    conversation_history: Optional[list[dict]] = None,
) -> AsyncGenerator[str, None]:
    """Stream an AI response token-by-token using Dedalus Labs streaming.

    Yields SSE-formatted lines:
      - data: {"type":"token","content":"..."}   for each text chunk
      - data: {"type":"actions","actions":[...]}  after tool execution finishes
      - data: {"type":"done"}                     when complete
    """
    financial_context = _build_financial_context(supabase, user_id)

    full_prompt = f"""{SYSTEM_PROMPT.replace("{username}", username)}

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

    mcp_configs = [
        ["jclim/VetoMCP", "tpparikh/abc", "tpparikh/-visaMCP"],
        ["jclim/VetoMCP", "tpparikh/-visaMCP"],
        ["jclim/VetoMCP"],
        ["tpparikh/abc", "tpparikh/-visaMCP"],
        [],
    ]

    full_text = ""
    stream_started = False

    for servers in mcp_configs:
        try:
            # runner.run(stream=True) returns an AsyncIterator directly (not a coroutine)
            stream = runner.run(
                model="gpt-5-nano",
                input=full_prompt,
                mcp_servers=servers,
                stream=True,
            )

            async for chunk in stream:
                # Dedalus SDK uses OpenAI-compatible chunk format:
                # chunk.choices[0].delta.content
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        token = delta.content
                        stream_started = True
                        full_text += token
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            break  # Success — stop trying fallbacks
        except Exception as e:
            print(f"[AGENT STREAM] MCP servers {servers} failed: {e}, trying fallback...")
            continue

    if not stream_started:
        # All streaming configs failed — fall back to non-streaming
        response_text, executed_actions = await generate_response(
            supabase, user_id, username, user_message, conversation_history
        )
        yield f"data: {json.dumps({'type': 'token', 'content': response_text})}\n\n"
        if executed_actions:
            yield f"data: {json.dumps({'type': 'actions', 'actions': executed_actions})}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"
        return

    # Parse actions from the full accumulated text
    response_text, action = _parse_action(full_text)
    executed_actions: list[dict] = []

    if action:
        action_result = _execute_action(supabase, user_id, action)
        executed_actions.append(action_result)

    if executed_actions:
        yield f"data: {json.dumps({'type': 'actions', 'actions': executed_actions})}\n\n"

    yield "data: {\"type\":\"done\"}\n\n"
