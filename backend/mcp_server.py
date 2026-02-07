import json
from typing import Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP, Context

from database import get_supabase
from models import (
    TransactionType,
    TransactionCreate,
    RuleType,
    BudgetRuleCreate,
    AuthorizationStatus,
    AgentSettingsCreate,
    AgentSettingsUpdate,
    AuthorizationLogCreate,
)
from services import transaction_service, budget_rule_service, agent_guard_service

# Initialize FastMCP server
mcp = FastMCP("Veto Budget Agent")

# ══════════════════════════════════════════════════════════════════════════════
# SERVER TOOLS (require database access)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def add_transaction(
    amount: float,
    description: str,
    category: str,
    transaction_type: str,
    username: str = "default_user",
    date: Optional[datetime] = None,
) -> str:
    """
    Record a new financial transaction (expense or income).

    Args:
        amount: The monetary value of the transaction.
        description: A brief description of what the transaction was for.
        category: The budget category (e.g., "Food", "Transport").
        transaction_type: Either "expense" or "income".
        username: The user's identifier (defaults to "default_user").
        date: Optional date of the transaction (defaults to now).
    """
    try:
        try:
            type_enum = TransactionType(transaction_type.lower())
        except ValueError:
            return f"Error: Invalid transaction type '{transaction_type}'. Must be 'expense' or 'income'."

        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        tx_data = TransactionCreate(
            amount=amount,
            description=description,
            category=category,
            transaction_type=type_enum,
            date=date
        )
        result = transaction_service.add_transaction(supabase, user_id, tx_data)
        return f"Transaction added: {result.description} ({result.amount}) - ID: {result.id}"
    except Exception as e:
        return f"Error adding transaction: {str(e)}"

@mcp.tool()
def delete_transaction(transaction_id: str, username: str = "default_user") -> str:
    """Delete a transaction by its ID."""
    try:
        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        success = transaction_service.delete_transaction(supabase, user_id, transaction_id)
        if success:
            return f"Transaction {transaction_id} deleted successfully."
        else:
            return f"Transaction {transaction_id} not found or access denied."
    except Exception as e:
        return f"Error deleting transaction: {str(e)}"

@mcp.tool()
def get_transactions(
    username: str = "default_user",
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    limit: int = 10
) -> str:
    """List recent transactions with optional filtering."""
    try:
        type_enum = None
        if transaction_type:
            try:
                type_enum = TransactionType(transaction_type.lower())
            except ValueError:
                return f"Error: Invalid transaction type '{transaction_type}'."

        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        txs = transaction_service.get_transactions(
            supabase,
            user_id,
            category=category,
            transaction_type=type_enum
        )

        if not txs:
            return "No transactions found."

        txs = txs[:limit]

        output = [f"Found {len(txs)} transactions:"]
        for tx in txs:
            date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
            output.append(f"- [{date_str}] {tx.description}: ${tx.amount} ({tx.category}) [{tx.transaction_type.value}] ID: {tx.id}")

        return "\n".join(output)
    except Exception as e:
        return f"Error fetching transactions: {str(e)}"



@mcp.tool()
def get_dashboard_summary(username: str = "default_user") -> str:
    """Get a financial dashboard summary including income, expenses, and rule compliance."""
    try:
        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        compliance = budget_rule_service.check_rule_compliance(supabase, user_id)
 
        lines = [
            "**Dashboard Summary**",
            f"Total Income: ${compliance['total_income']:.2f}",
            f"Total Expenses: ${compliance['total_expenses']:.2f}",
            f"Net: ${compliance['net']:.2f}",
            "",
            "**Budget Rules Status:**"
        ]
 
        for rule in compliance['rules']:
            status = "COMPLIANT" if rule.get("compliant") else "AT RISK/NON-COMPLIANT"
            lines.append(f"- {rule.get('rule_name')} ({rule.get('rule_type')}): {status}")
            if rule.get("message"):
                lines.append(f"  Note: {rule.get('message')}")
 
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching dashboard: {str(e)}"

# ── Budget Rules Server Tools ────────────────────────────────────────────────

@mcp.tool()
def create_budget_rule(
    rule_type: str,
    name: str,
    config: str,
    username: str = "default_user"
) -> str:
    """
    Create a new budget rule.

    Args:
        rule_type: One of "percentage_allocation", "category_limit", "savings_goal", "spending_alert"
        name: A friendly name for the rule (e.g., "50/30/20 Rule")
        config: JSON string with rule configuration. Examples:
            - percentage_allocation: {"needs": 50, "wants": 30, "savings": 20}
            - category_limit: {"category": "Food", "limit": 500}
            - savings_goal: {"goal": 1000}
            - spending_alert: {"category": "Entertainment", "threshold": 200}
        username: The user's identifier.
    """
    try:
        try:
            type_enum = RuleType(rule_type.lower())
        except ValueError:
            valid = ", ".join([r.value for r in RuleType])
            return f"Error: Invalid rule type '{rule_type}'. Must be one of: {valid}"

        # Validate JSON
        try:
            json.loads(config)
        except json.JSONDecodeError:
            return "Error: config must be a valid JSON string."

        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)

        # Special handling for 50/30/20 split
        if type_enum == RuleType.percentage_allocation and "50/30/20" in config:
            # Create 3 separate rules
            rules_created = []

            # 1. Needs
            r1 = BudgetRuleCreate(rule_type=RuleType.percentage_needs, name="Needs Limit (50%)", config=json.dumps({"percent": 50}))
            res1 = budget_rule_service.create_rule(supabase, user_id, r1)
            rules_created.append(res1.name)

            # 2. Wants
            r2 = BudgetRuleCreate(rule_type=RuleType.percentage_wants, name="Wants Limit (30%)", config=json.dumps({"percent": 30}))
            res2 = budget_rule_service.create_rule(supabase, user_id, r2)
            rules_created.append(res2.name)

            # 3. Savings (using generic percentage_allocation or specific? Let's use percentage_allocation as "Savings" for now to match compliance logic default)
            # Actually, I added percentage_savings logic? No, check_rule_compliance still uses percentage_allocation for savings.
            # Let's verify what I did in budget_rule_service.
            # I kept "elif rule_type == RuleType.percentage_allocation.value:" for savings logic.
            r3 = BudgetRuleCreate(rule_type=RuleType.percentage_allocation, name="Savings Goal (20%)", config=json.dumps({"savings": 20}))
            res3 = budget_rule_service.create_rule(supabase, user_id, r3)
            rules_created.append(res3.name)

            return f"Created 3 budget rules: {', '.join(rules_created)}"

        rule_data = BudgetRuleCreate(
            rule_type=type_enum,
            name=name,
            config=config
        )
        result = budget_rule_service.create_rule(supabase, user_id, rule_data)
        return f"Budget rule '{result.name}' created successfully (ID: {result.id})."
    except Exception as e:
        return f"Error creating budget rule: {str(e)}"

@mcp.tool()
def get_budget_rules(username: str = "default_user") -> str:
    """List all active budget rules for a user."""
    try:
        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        output = []

        # Get explicit budget rules
        rules = budget_rule_service.get_rules(supabase, user_id)
        if rules:
            output.append("**Budget Rules:**")
            for r in rules:
                output.append(f"- [{r.rule_type.value}] {r.name} (ID: {r.id})")
                output.append(f"  Config: {r.config}")
        
        if not rules:
            return "No budget rules set."

        return "\n".join(output)
    except Exception as e:
        return f"Error fetching budget rules: {str(e)}"

@mcp.tool()
def delete_budget_rule(rule_id: str, username: str = "default_user") -> str:
    """Delete a budget rule by its ID."""
    try:
        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        success = budget_rule_service.delete_rule(supabase, user_id, rule_id)
        if success:
            return f"Budget rule {rule_id} deleted successfully."
        else:
            return f"Budget rule {rule_id} not found or access denied."
    except Exception as e:
        return f"Error deleting budget rule: {str(e)}"

@mcp.tool()
def check_rule_compliance(username: str = "default_user") -> str:
    """
    Check if the user is following their active budget rules.
    Returns compliance status for each rule.
    """
    try:
        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        result = budget_rule_service.check_rule_compliance(supabase, user_id)

        if result.get("status") == "no_rules":
            return result.get("message", "No active budget rules found.")

        lines = ["**Budget Rule Compliance Report**", ""]
        for rule in result.get("rules", []):
            status = "Compliant" if rule.get("compliant") else "Not Compliant"
            if rule.get("compliant") is None:
                status = "Cannot determine"
            lines.append(f"**{rule.get('rule_name')}** ({rule.get('rule_type')}): {status}")

            # Add details based on rule type
            if rule.get("rule_type") == "percentage_allocation":
                lines.append(f"  Target savings: {rule.get('target_savings_pct')}% | Actual: {rule.get('actual_savings_pct')}%")
            elif rule.get("rule_type") == "category_limit":
                lines.append(f"  {rule.get('category')}: ${rule.get('spent')} / ${rule.get('limit')}")
            elif rule.get("rule_type") == "savings_goal":
                lines.append(f"  Saved: ${rule.get('saved')} / Goal: ${rule.get('goal')}")
            elif rule.get("rule_type") == "spending_alert":
                alert = "ALERT TRIGGERED" if rule.get("alert_triggered") else "No alert"
                lines.append(f"  {rule.get('category')}: ${rule.get('spent')} (threshold: ${rule.get('threshold')}) - {alert}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"Error checking compliance: {str(e)}"

@mcp.tool()
def get_spending_insights(username: str = "default_user") -> str:
    """
    Get AI-friendly spending insights and patterns.
    Useful for providing proactive budget advice.
    """
    try:
        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        compliance = budget_rule_service.check_rule_compliance(supabase, user_id)
        total_income = compliance["total_income"]
        total_expenses = compliance["total_expenses"]

        insights = []

        # Overall health
        if total_income > 0:
            savings_rate = ((total_income - total_expenses) / total_income) * 100
            if savings_rate >= 20:
                insights.append(f"Great savings rate of {savings_rate:.1f}%!")
            elif savings_rate >= 10:
                insights.append(f"Savings rate is {savings_rate:.1f}%. Consider increasing to 20%.")
            elif savings_rate > 0:
                insights.append(f"Low savings rate of {savings_rate:.1f}%. Try to save more.")
            else:
                insights.append(f"Negative savings rate ({savings_rate:.1f}%). Spending exceeds income!")
        else:
            insights.append("No income recorded yet.")

        # Rule analysis
        rules = compliance.get("rules", [])
        if rules:
            # Find rules that are non-compliant
            non_compliant = [r for r in rules if r.get("compliant") is False]
            if non_compliant:
                for r in non_compliant:
                    insights.append(f"Rule '{r.get('rule_name')}' is broken: {r.get('message', 'Check rule details.')}")


        if not insights:
            return "No spending data available yet."

        return "**Spending Insights**\n" + "\n".join(insights)
    except Exception as e:
        return f"Error generating insights: {str(e)}"

# ══════════════════════════════════════════════════════════════════════════════
# LOCAL TOOLS (no database, pure logic - for client-side AI decisions)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_budget_methods() -> str:
    """
    Returns a list of popular budget methods with descriptions.
    Useful for guiding users during onboarding when choosing a budget strategy.
    This is a LOCAL TOOL - no database access required.
    """
    methods = [
        {
            "name": "50/30/20 Rule",
            "description": "Allocate 50% of income to needs (rent, groceries, utilities), 30% to wants (entertainment, dining out), and 20% to savings and debt repayment.",
            "best_for": "Beginners who want a simple framework.",
            "config_template": '{"needs": 50, "wants": 30, "savings": 20}'
        },
        {
            "name": "Zero-Based Budgeting",
            "description": "Assign every dollar a specific purpose until income minus expenses equals zero. Every dollar has a job.",
            "best_for": "Detail-oriented planners who want full control.",
            "config_template": '{"method": "zero_based"}'
        },
        {
            "name": "Envelope System",
            "description": "Allocate cash to category 'envelopes'. When an envelope is empty, no more spending in that category.",
            "best_for": "People who struggle with overspending in specific categories.",
            "config_template": '{"categories": ["Groceries", "Entertainment", "Dining Out"]}'
        },
        {
            "name": "Pay Yourself First",
            "description": "Automatically save a fixed percentage of income before spending on anything else.",
            "best_for": "Those prioritizing savings and wealth building.",
            "config_template": '{"savings_percent": 20}'
        },
        {
            "name": "80/20 Rule",
            "description": "Save 20% of income, spend 80% however you want. Simple and flexible.",
            "best_for": "People who want minimal budgeting effort.",
            "config_template": '{"savings": 20, "spending": 80}'
        },
        {
            "name": "Values-Based Budgeting",
            "description": "Prioritize spending on what matters most to you. Cut ruthlessly elsewhere.",
            "best_for": "Those who want alignment between money and values.",
            "config_template": '{"priorities": ["Health", "Education", "Experiences"]}'
        }
    ]
    return json.dumps(methods, indent=2)

@mcp.tool()
def check_budget_for_purchase(
    budget_limit: float,
    amount_spent: float,
    purchase_amount: float,
    category: str = "General"
) -> str:
    """
    Check if a purchase is within budget.
    LOCAL TOOL - no database access, pure calculation.

    Args:
        budget_limit: The monthly budget limit for this category.
        amount_spent: How much has already been spent in this category.
        purchase_amount: The cost of the proposed purchase.
        category: The category name (for display purposes).

    Returns:
        A recommendation on whether to proceed with the purchase.
    """
    remaining = budget_limit - amount_spent
    after_purchase = remaining - purchase_amount

    result = {
        "category": category,
        "budget_limit": budget_limit,
        "already_spent": amount_spent,
        "remaining_before": remaining,
        "purchase_amount": purchase_amount,
        "remaining_after": after_purchase,
    }

    if purchase_amount > remaining:
        result["recommendation"] = "DENY"
        result["reason"] = f"This purchase of ${purchase_amount:.2f} would exceed your {category} budget by ${abs(after_purchase):.2f}."
    elif after_purchase < (budget_limit * 0.1):
        result["recommendation"] = "CAUTION"
        result["reason"] = f"This purchase is within budget, but would leave only ${after_purchase:.2f} ({(after_purchase/budget_limit)*100:.1f}%) remaining."
    else:
        result["recommendation"] = "APPROVE"
        result["reason"] = f"This purchase is within budget. You'll have ${after_purchase:.2f} remaining."

    return json.dumps(result, indent=2)

@mcp.tool()
def suggest_budget_allocation(
    monthly_income: float,
    method: str = "50/30/20"
) -> str:
    """
    Suggest budget allocations based on income and chosen method.
    LOCAL TOOL - no database access.

    Args:
        monthly_income: The user's monthly income.
        method: Budget method to use ("50/30/20", "80/20", "pay_yourself_first").
    """
    allocations = {}

    if method == "50/30/20":
        allocations = {
            "needs": {"percent": 50, "amount": monthly_income * 0.50},
            "wants": {"percent": 30, "amount": monthly_income * 0.30},
            "savings": {"percent": 20, "amount": monthly_income * 0.20},
        }
    elif method == "80/20":
        allocations = {
            "spending": {"percent": 80, "amount": monthly_income * 0.80},
            "savings": {"percent": 20, "amount": monthly_income * 0.20},
        }
    elif method == "pay_yourself_first":
        allocations = {
            "savings": {"percent": 25, "amount": monthly_income * 0.25},
            "remainder": {"percent": 75, "amount": monthly_income * 0.75},
        }
    else:
        return json.dumps({"error": f"Unknown method: {method}. Try '50/30/20', '80/20', or 'pay_yourself_first'."})

    result = {
        "monthly_income": monthly_income,
        "method": method,
        "allocations": allocations
    }
    return json.dumps(result, indent=2)

@mcp.tool()
def get_budget_health_score(
    total_income: float,
    total_expenses: float,
    categories_over_budget: int = 0,
    has_emergency_fund: bool = False,
    debt_to_income_ratio: float = 0.0
) -> str:
    """
    Calculate a 0-100 financial health score.
    LOCAL TOOL - no database access.

    Args:
        total_income: Total monthly income.
        total_expenses: Total monthly expenses.
        categories_over_budget: Number of categories currently over budget.
        has_emergency_fund: Whether user has 3+ months of expenses saved.
        debt_to_income_ratio: Monthly debt payments / monthly income (0.0 to 1.0).
    """
    score = 50  # Start at neutral

    # Savings rate impact (-20 to +30)
    if total_income > 0:
        savings_rate = (total_income - total_expenses) / total_income
        if savings_rate >= 0.20:
            score += 30
        elif savings_rate >= 0.10:
            score += 15
        elif savings_rate >= 0:
            score += 5
        else:
            score -= 20  # Spending more than earning

    # Categories over budget (-15)
    score -= min(categories_over_budget * 5, 15)

    # Emergency fund (+15)
    if has_emergency_fund:
        score += 15

    # Debt-to-income ratio (-20 to 0)
    if debt_to_income_ratio > 0.50:
        score -= 20
    elif debt_to_income_ratio > 0.30:
        score -= 10
    elif debt_to_income_ratio > 0.15:
        score -= 5

    # Clamp score
    score = max(0, min(100, score))

    # Determine grade
    if score >= 80:
        grade = "A"
        message = "Excellent financial health! Keep it up."
    elif score >= 60:
        grade = "B"
        message = "Good financial health with room for improvement."
    elif score >= 40:
        grade = "C"
        message = "Fair financial health. Consider reviewing your budget."
    elif score >= 20:
        grade = "D"
        message = "Poor financial health. Immediate action recommended."
    else:
        grade = "F"
        message = "Critical financial situation. Seek professional advice."

    result = {
        "score": score,
        "grade": grade,
        "message": message,
        "factors": {
            "savings_rate_impact": "positive" if total_income > 0 and (total_income - total_expenses) > 0 else "negative",
            "over_budget_categories": categories_over_budget,
            "emergency_fund": has_emergency_fund,
            "debt_to_income": debt_to_income_ratio
        }
    }
    return json.dumps(result, indent=2)

@mcp.tool()
def project_monthly_spending(
    current_day_of_month: int,
    days_in_month: int,
    amount_spent_so_far: float,
    budget_limit: float
) -> str:
    """
    Project end-of-month spending based on current pace.
    LOCAL TOOL - no database access.

    Args:
        current_day_of_month: What day of the month it is (1-31).
        days_in_month: Total days in this month (28-31).
        amount_spent_so_far: How much has been spent so far this month.
        budget_limit: The monthly budget limit.
    """
    if current_day_of_month <= 0:
        return json.dumps({"error": "current_day_of_month must be positive"})

    daily_rate = amount_spent_so_far / current_day_of_month
    projected_total = daily_rate * days_in_month
    difference = budget_limit - projected_total

    result = {
        "current_day": current_day_of_month,
        "days_in_month": days_in_month,
        "spent_so_far": amount_spent_so_far,
        "daily_average": round(daily_rate, 2),
        "projected_month_total": round(projected_total, 2),
        "budget_limit": budget_limit,
        "projected_difference": round(difference, 2),
    }

    if difference >= 0:
        result["status"] = "ON_TRACK"
        result["message"] = f"At current pace, you'll finish ${difference:.2f} under budget."
    else:
        result["status"] = "OVER_BUDGET"
        result["message"] = f"Warning: At current pace, you'll be ${abs(difference):.2f} over budget."
        # Calculate how much to reduce daily spending
        remaining_days = days_in_month - current_day_of_month
        if remaining_days > 0:
            remaining_budget = budget_limit - amount_spent_so_far
            safe_daily = remaining_budget / remaining_days
            result["recommended_daily_limit"] = round(max(0, safe_daily), 2)

    return json.dumps(result, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# AGENT GUARD RAILS — Tools for autonomous agents to check budget compliance
# These are advisory tools that external agents should call BEFORE making purchases
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def authorize_purchase(
    username: str,
    amount: float,
    category: str,
    merchant: Optional[str] = None,
    description: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> str:
    """
    Check if a purchase is authorized within the user's budget.
    
    AGENT GUARD RAIL — This is an advisory tool. External agents SHOULD call this
    before making any purchase on behalf of a user. The tool checks:
    1. Category budget limits
    2. Overall monthly budget
    3. Risk factors
    
    Returns a recommendation: APPROVED, DENIED, CAUTION, or REQUIRES_HUMAN_APPROVAL.
    
    Args:
        username: The user's identifier (required).
        amount: The purchase amount in dollars.
        category: The spending category (e.g., "Food", "Entertainment").
        merchant: Optional merchant name for context.
        description: Optional description of the purchase.
        agent_id: Optional identifier for the requesting agent.
    
    Returns:
        JSON with authorization status, reason, and remaining budgets.
    """
    from uuid import uuid4

    try:
        supabase = get_supabase()
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)

        # Get user's budget compliance status
        compliance = budget_rule_service.check_rule_compliance(supabase, user_id)
        net_balance = compliance["net"]
        
        # Find if there is a category limit rule for this category
        category_rule = None
        for rule in compliance["rules"]:
            if rule.get("rule_type") == "category_limit" and rule.get("category", "").lower() == category.lower():
                category_rule = rule
                break
        
        # Default agent spending limits (can be made configurable later)
        default_limits = {
            "single_transaction_limit": 50.0,
            "daily_limit": 100.0,
            "require_approval_above": 100.0,
        }
        
        authorization_token = uuid4().hex
        
        result = {
            "authorization_token": authorization_token,
            "username": username,
            "amount": amount,
            "category": category,
            "merchant": merchant,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Check 1: Single transaction limit
        if amount > default_limits["single_transaction_limit"]:
            result["status"] = "REQUIRES_HUMAN_APPROVAL"
            result["reason"] = f"Purchase of ${amount:.2f} exceeds the agent single-transaction limit of ${default_limits['single_transaction_limit']:.2f}. Human approval required."
            result["budget_remaining"] = net_balance
            return json.dumps(result, indent=2)
        
        # Check 2: Category budget (if exists)
        if category_rule:
            limit = category_rule.get("limit", 0)
            spent = category_rule.get("spent", 0)
            remaining = start_remaining = limit - spent
            
            # If already over budget, remainng is negative.
            # If remaining is positive, we check if purchase fits.
            
            if amount > remaining:
                result["status"] = "DENIED"
                result["reason"] = f"Purchase of ${amount:.2f} would exceed your {category} budget. Only ${remaining:.2f} remaining."
                result["category_remaining"] = remaining
                result["budget_remaining"] = net_balance
                return json.dumps(result, indent=2)
            elif remaining - amount < (limit * 0.1):
                result["status"] = "CAUTION"
                result["reason"] = f"Purchase is within budget, but would leave only ${remaining - amount:.2f} in {category}. Proceed with caution."
                result["category_remaining"] = remaining - amount
                result["budget_remaining"] = net_balance
                return json.dumps(result, indent=2)
            else:
                result["category_remaining"] = remaining - amount
        
        # Check 3: Overall budget health
        if net_balance < 0:
            result["status"] = "CAUTION"
            result["reason"] = f"Your overall budget is in deficit (${net_balance:.2f}). Consider this purchase carefully."
            result["budget_remaining"] = net_balance
            return json.dumps(result, indent=2)
        
        # All checks passed
        result["status"] = "APPROVED"
        result["reason"] = f"Purchase of ${amount:.2f} in {category} is within budget."
        result["budget_remaining"] = net_balance - amount
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "reason": f"Unable to verify budget: {str(e)}",
            "authorization_token": None
        }, indent=2)


@mcp.tool()
def get_agent_spending_limits(username: str = "default_user") -> str:
    """
    Get the spending limits configured for autonomous agents.
    
    AGENT GUARD RAIL — Agents should call this to understand what limits apply
    before attempting purchases on behalf of the user.
    
    Args:
        username: The user's identifier.
    
    Returns:
        JSON with daily, weekly, monthly, and per-transaction limits.
    """
    # Default limits (can be made user-configurable with database later)
    limits = {
        "username": username,
        "single_transaction_limit": 50.0,
        "daily_limit": 100.0,
        "weekly_limit": 500.0,
        "monthly_limit": 2000.0,
        "require_approval_above": 100.0,
        "allowed_categories": None,  # None = all allowed
        "blocked_categories": [],
        "note": "These are default limits. User-configurable limits will be available in a future update."
    }
    return json.dumps(limits, indent=2)


@mcp.tool()
def assess_purchase_risk(
    amount: float,
    category: str,
    monthly_income: float = 0.0,
    monthly_expenses: float = 0.0,
    is_recurring: bool = False,
    is_essential: bool = False,
) -> str:
    """
    Assess the risk level of a proposed purchase.
    
    AGENT GUARD RAIL — Returns a risk score (0-100) and risk level to help agents
    make informed decisions about purchases.
    
    Args:
        amount: The purchase amount.
        category: The spending category.
        monthly_income: User's monthly income (for context).
        monthly_expenses: User's current monthly expenses (for context).
        is_recurring: Whether this is a recurring purchase.
        is_essential: Whether this is an essential purchase (needs vs wants).
    
    Returns:
        JSON with risk_score (0-100), risk_level, and risk_factors.
    """
    risk_score = 0
    risk_factors = []
    
    # Factor 1: Amount relative to income (0-30 points)
    if monthly_income > 0:
        income_ratio = amount / monthly_income
        if income_ratio > 0.25:
            risk_score += 30
            risk_factors.append(f"Purchase is {income_ratio*100:.1f}% of monthly income (very high)")
        elif income_ratio > 0.10:
            risk_score += 20
            risk_factors.append(f"Purchase is {income_ratio*100:.1f}% of monthly income (high)")
        elif income_ratio > 0.05:
            risk_score += 10
            risk_factors.append(f"Purchase is {income_ratio*100:.1f}% of monthly income (moderate)")
    else:
        risk_score += 15
        risk_factors.append("No income data available for context")
    
    # Factor 2: Expense vs income ratio (0-25 points)
    if monthly_income > 0 and monthly_expenses > 0:
        expense_ratio = (monthly_expenses + amount) / monthly_income
        if expense_ratio > 1.0:
            risk_score += 25
            risk_factors.append("Would push total expenses above income")
        elif expense_ratio > 0.9:
            risk_score += 15
            risk_factors.append("Would push expenses to 90%+ of income")
        elif expense_ratio > 0.8:
            risk_score += 5
            risk_factors.append("Expenses would be 80-90% of income")
    
    # Factor 3: Category risk (0-20 points)
    high_risk_categories = ["gambling", "alcohol", "tobacco", "cryptocurrency"]
    medium_risk_categories = ["entertainment", "dining out", "luxury", "shopping"]
    
    cat_lower = category.lower()
    if any(cat in cat_lower for cat in high_risk_categories):
        risk_score += 20
        risk_factors.append(f"Category '{category}' is flagged as high-risk")
    elif any(cat in cat_lower for cat in medium_risk_categories):
        risk_score += 10
        risk_factors.append(f"Category '{category}' is discretionary spending")
    
    # Factor 4: Recurring commitment (0-15 points)
    if is_recurring:
        risk_score += 15
        risk_factors.append("Recurring purchase creates ongoing commitment")
    
    # Factor 5: Essential vs wants (-10 to +10 points)
    if is_essential:
        risk_score = max(0, risk_score - 10)
        risk_factors.append("Essential purchase (reduced risk)")
    else:
        risk_score += 5
        risk_factors.append("Non-essential purchase")
    
    # Determine risk level
    risk_score = min(100, max(0, risk_score))
    
    if risk_score >= 70:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    result = {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "amount": amount,
        "category": category,
        "recommendation": "PROCEED" if risk_score < 50 else "REVIEW" if risk_score < 70 else "AVOID"
    }
    
    return json.dumps(result, indent=2)


@mcp.tool()
def validate_agent_action(
    action_type: str,
    amount: float,
    category: str = "General",
    agent_id: Optional[str] = None,
) -> str:
    """
    Validate whether an agent action is permitted under current rules.
    
    AGENT GUARD RAIL — Generic validator for any agent financial action.
    
    Args:
        action_type: Type of action ("purchase", "transfer", "subscription", "recurring_payment").
        amount: The monetary amount involved.
        category: The spending category.
        agent_id: Optional identifier for the requesting agent.
    
    Returns:
        JSON with is_permitted, reason, and any restrictions.
    """
    valid_action_types = ["purchase", "transfer", "subscription", "recurring_payment"]
    
    if action_type.lower() not in valid_action_types:
        return json.dumps({
            "is_permitted": False,
            "reason": f"Unknown action type '{action_type}'. Valid types: {', '.join(valid_action_types)}",
            "action_type": action_type,
        }, indent=2)
    
    # Default restrictions
    restrictions = {
        "purchase": {"max_amount": 50.0, "requires_approval_above": 50.0},
        "transfer": {"max_amount": 100.0, "requires_approval_above": 25.0},
        "subscription": {"max_amount": 20.0, "requires_approval_above": 10.0},
        "recurring_payment": {"max_amount": 100.0, "requires_approval_above": 50.0},
    }
    
    action_restrictions = restrictions.get(action_type.lower(), {})
    max_amount = action_restrictions.get("max_amount", 50.0)
    approval_threshold = action_restrictions.get("requires_approval_above", 50.0)
    
    result = {
        "action_type": action_type,
        "amount": amount,
        "category": category,
        "agent_id": agent_id,
        "max_allowed": max_amount,
        "approval_threshold": approval_threshold,
    }
    
    if amount > max_amount:
        result["is_permitted"] = False
        result["reason"] = f"Amount ${amount:.2f} exceeds maximum allowed ${max_amount:.2f} for {action_type}."
        result["requires_human_approval"] = True
    elif amount > approval_threshold:
        result["is_permitted"] = True
        result["reason"] = f"Action is permitted but exceeds ${approval_threshold:.2f}. Human notification recommended."
        result["requires_human_approval"] = True
    else:
        result["is_permitted"] = True
        result["reason"] = f"Action is within agent limits."
        result["requires_human_approval"] = False
    
    return json.dumps(result, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# AGENT GUARD RAILS — Database-backed tools for managing agent settings
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def set_agent_spending_limits(
    username: str,
    single_transaction_limit: Optional[float] = None,
    daily_limit: Optional[float] = None,
    weekly_limit: Optional[float] = None,
    monthly_limit: Optional[float] = None,
    require_approval_above: Optional[float] = None,
) -> str:
    """
    Set or update spending limits for autonomous agents.
    
    AGENT GUARD RAIL — Allows users to configure how much agents can spend on their behalf.
    
    Args:
        username: The user's identifier.
        single_transaction_limit: Max amount per transaction (default $50).
        daily_limit: Max daily spending by agents (default $100).
        weekly_limit: Max weekly spending by agents (default $500).
        monthly_limit: Max monthly spending by agents (default $2000).
        require_approval_above: Require human approval above this amount (default $100).
    
    Returns:
        JSON with the updated agent settings.
    """
    try:
        supabase = get_supabase()
        
        # Look up user ID from username
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        
        # Check if settings exist
        existing = agent_guard_service.get_agent_settings(supabase, user_id)
        
        if existing:
            # Update existing settings
            update_data = AgentSettingsUpdate(
                single_transaction_limit=single_transaction_limit,
                daily_limit=daily_limit,
                weekly_limit=weekly_limit,
                monthly_limit=monthly_limit,
                require_approval_above=require_approval_above,
            )
            result = agent_guard_service.update_agent_settings(supabase, user_id, update_data)
        else:
            # Create new settings
            create_data = AgentSettingsCreate(
                single_transaction_limit=single_transaction_limit or 50.0,
                daily_limit=daily_limit or 100.0,
                weekly_limit=weekly_limit or 500.0,
                monthly_limit=monthly_limit or 2000.0,
                require_approval_above=require_approval_above or 100.0,
            )
            result = agent_guard_service.create_agent_settings(supabase, user_id, create_data)
        
        if result:
            return json.dumps({
                "success": True,
                "message": "Agent spending limits updated.",
                "settings": {
                    "single_transaction_limit": result.single_transaction_limit,
                    "daily_limit": result.daily_limit,
                    "weekly_limit": result.weekly_limit,
                    "monthly_limit": result.monthly_limit,
                    "require_approval_above": result.require_approval_above,
                }
            }, indent=2)
        else:
            return json.dumps({"success": False, "error": "Failed to update settings"}, indent=2)
            
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def get_agent_settings(username: str = "default_user") -> str:
    """
    Get the current agent spending settings for a user.
    
    AGENT GUARD RAIL — Returns all configured limits and restrictions.
    
    Args:
        username: The user's identifier.
    
    Returns:
        JSON with all agent settings including limits and category restrictions.
    """
    try:
        supabase = get_supabase()
        
        # Look up user ID from username
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        settings = agent_guard_service.get_or_create_agent_settings(supabase, user_id)
        
        return json.dumps({
            "username": username,
            "single_transaction_limit": settings.single_transaction_limit,
            "daily_limit": settings.daily_limit,
            "weekly_limit": settings.weekly_limit,
            "monthly_limit": settings.monthly_limit,
            "require_approval_above": settings.require_approval_above,
            "allowed_categories": settings.allowed_categories,
            "blocked_categories": settings.blocked_categories,
            "is_active": settings.is_active,
        }, indent=2)
        
    except Exception as e:
        # Return default limits if database is not available
        return json.dumps({
            "username": username,
            "single_transaction_limit": 50.0,
            "daily_limit": 100.0,
            "weekly_limit": 500.0,
            "monthly_limit": 2000.0,
            "require_approval_above": 100.0,
            "allowed_categories": None,
            "blocked_categories": [],
            "is_active": True,
            "note": f"Using default limits (database unavailable: {str(e)})"
        }, indent=2)


@mcp.tool()
def log_agent_authorization(
    username: str,
    action_type: str,
    amount: float,
    status: str,
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    reason: Optional[str] = None,
    authorization_token: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> str:
    """
    Log an agent authorization attempt for audit purposes.
    
    AGENT GUARD RAIL — Creates an audit trail of all agent spending attempts.
    
    Args:
        username: The user's identifier.
        action_type: Type of action ("purchase", "transfer", "subscription").
        amount: The monetary amount.
        status: Authorization status ("APPROVED", "DENIED", "CAUTION", "REQUIRES_HUMAN_APPROVAL").
        category: The spending category.
        merchant: The merchant name.
        reason: Explanation for the authorization decision.
        authorization_token: Unique token for this authorization.
        agent_id: Identifier of the requesting agent.
    
    Returns:
        JSON confirming the log entry was created.
    """
    try:
        supabase = get_supabase()
        
        # Look up user ID from username
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        
        # Parse status
        try:
            status_enum = AuthorizationStatus(status.upper())
        except ValueError:
            status_enum = AuthorizationStatus.ERROR
        
        log_data = AuthorizationLogCreate(
            agent_id=agent_id,
            action_type=action_type,
            amount=amount,
            category=category,
            merchant=merchant,
            status=status_enum,
            reason=reason,
            authorization_token=authorization_token,
        )
        
        result = agent_guard_service.log_authorization(supabase, user_id, log_data)
        
        return json.dumps({
            "success": True,
            "log_id": result.id,
            "authorization_token": result.authorization_token,
            "message": f"Authorization logged: {status} for ${amount:.2f} {action_type}"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def get_agent_authorization_history(
    username: str,
    limit: int = 20,
    status_filter: Optional[str] = None,
) -> str:
    """
    Get the authorization history for a user's agents.
    
    AGENT GUARD RAIL — Shows all past authorization attempts for auditing.
    
    Args:
        username: The user's identifier.
        limit: Maximum number of records to return (default 20).
        status_filter: Optional filter by status ("APPROVED", "DENIED", etc.).
    
    Returns:
        JSON with list of authorization attempts.
    """
    try:
        supabase = get_supabase()
        
        # Look up user ID from username
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        
        history = agent_guard_service.get_authorization_history(
            supabase, user_id, limit=limit, status_filter=status_filter
        )
        
        records = []
        for entry in history:
            records.append({
                "id": entry.id,
                "agent_id": entry.agent_id,
                "action_type": entry.action_type,
                "amount": entry.amount,
                "category": entry.category,
                "merchant": entry.merchant,
                "status": entry.status,
                "reason": entry.reason,
                "was_executed": entry.was_executed,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            })
        
        return json.dumps({
            "username": username,
            "total_records": len(records),
            "history": records
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "history": []}, indent=2)


@mcp.tool()
def get_cumulative_agent_spend(
    username: str,
    period: str = "daily",
) -> str:
    """
    Get cumulative spending by agents for a time period.
    
    AGENT GUARD RAIL — Shows how much agents have spent on behalf of the user.
    
    Args:
        username: The user's identifier.
        period: Time period ("daily", "weekly", "monthly").
    
    Returns:
        JSON with cumulative spend and remaining limits.
    """
    try:
        supabase = get_supabase()
        
        # Look up user ID from username
        user_id = agent_guard_service.get_or_create_user_id(supabase, username)
        
        cumulative = agent_guard_service.get_cumulative_agent_spend(supabase, user_id, period)
        settings = agent_guard_service.get_or_create_agent_settings(supabase, user_id)
        
        if period == "daily":
            limit = settings.daily_limit
        elif period == "weekly":
            limit = settings.weekly_limit
        else:
            limit = settings.monthly_limit
        
        remaining = limit - cumulative
        
        return json.dumps({
            "username": username,
            "period": period,
            "cumulative_spend": cumulative,
            "period_limit": limit,
            "remaining": max(0, remaining),
            "limit_reached": cumulative >= limit,
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "username": username,
            "period": period,
            "cumulative_spend": 0,
            "error": str(e)
        }, indent=2)


if __name__ == "__main__":
    mcp.run()
