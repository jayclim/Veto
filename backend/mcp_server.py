from typing import Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP, Context
from sqlmodel import Session, create_engine, select

from database import engine
from models import TransactionType, TransactionCreate, BudgetCategoryCreate
from services import transaction_service, budget_service

# Initialize FastMCP server
mcp = FastMCP("Veto Budget Agent")

def get_session():
    return Session(engine)

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
        # Validate transaction type
        try:
            type_enum = TransactionType(transaction_type.lower())
        except ValueError:
            return f"Error: Invalid transaction type '{transaction_type}'. Must be 'expense' or 'income'."

        with get_session() as session:
            tx_data = TransactionCreate(
                amount=amount,
                description=description,
                category=category,
                transaction_type=type_enum,
                date=date
            )
            result = transaction_service.add_transaction(session, username, tx_data)
            return f"Transaction added: {result.description} ({result.amount}) - ID: {result.id}"
    except Exception as e:
        return f"Error adding transaction: {str(e)}"

@mcp.tool()
def delete_transaction(transaction_id: str, username: str = "default_user") -> str:
    """
    Delete a transaction by its ID.
    """
    try:
        with get_session() as session:
            success = transaction_service.delete_transaction(session, username, transaction_id)
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
    """
    List recent transactions with optional filtering.
    """
    try:
        type_enum = None
        if transaction_type:
            try:
                type_enum = TransactionType(transaction_type.lower())
            except ValueError:
                return f"Error: Invalid transaction type '{transaction_type}'."

        with get_session() as session:
            # Note: The service doesn't support 'limit' natively based on previous view, 
            # so we might wrap the service or just slice the result. 
            # Looking at service signature: get_transactions(session, user_id, category, transaction_type, start_date, end_date)
            # It returns a list.
            
            txs = transaction_service.get_transactions(
                session, 
                username, 
                category=category, 
                transaction_type=type_enum
            )
            
            # Simple text formatting
            if not txs:
                return "No transactions found."
            
            # Slice to limit
            txs = txs[:limit]
            
            output = [f"Found {len(txs)} transactions:"]
            for tx in txs:
                date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
                output.append(f"- [{date_str}] {tx.description}: ${tx.amount} ({tx.category}) [{tx.transaction_type.value}] ID: {tx.id}")
            
            return "\n".join(output)
    except Exception as e:
        return f"Error fetching transactions: {str(e)}"

@mcp.tool()
def create_budget_category(
    name: str,
    monthly_limit: float,
    username: str = "default_user"
) -> str:
    """
    Create a new budget category with a monthly spending limit.
    """
    try:
        with get_session() as session:
            cat_data = BudgetCategoryCreate(name=name, monthly_limit=monthly_limit)
            result = budget_service.create_category(session, username, cat_data)
            return f"Category '{result.name}' created with limit ${result.monthly_limit}."
    except Exception as e:
        return f"Error creating category: {str(e)}"

@mcp.tool()
def get_budget_categories(username: str = "default_user") -> str:
    """
    List all budget categories and their limits.
    """
    try:
        with get_session() as session:
            cats = budget_service.get_categories(session, username)
            if not cats:
                return "No categories set."
            
            output = ["Budget Categories:"]
            for c in cats:
                output.append(f"- {c.name}: ${c.monthly_limit}/month")
            return "\n".join(output)
    except Exception as e:
        return f"Error fetching categories: {str(e)}"

@mcp.tool()
def get_dashboard_summary(username: str = "default_user") -> str:
    """
    Get a financial dashboard summary including income, expenses, and category breakdowns.
    """
    try:
        with get_session() as session:
            summary = budget_service.get_dashboard_summary(session, username)
            
            lines = [
                "**Dashboard Summary**",
                f"Total Income: ${summary.total_income:.2f}",
                f"Total Expenses: ${summary.total_expenses:.2f}",
                f"Net: ${summary.net:.2f}",
                "",
                "**Category Breakdown:**"
            ]
            
            for cat in summary.categories:
                limit_str = f" / ${cat.budget_limit}" if cat.budget_limit else ""
                remaining_str = f" (Remaining: ${cat.remaining:.2f})" if cat.remaining is not None else ""
                lines.append(f"- {cat.category}: ${cat.total_spent:.2f}{limit_str}{remaining_str}")
                
            return "\n".join(lines)
    except Exception as e:
        return f"Error fetching dashboard: {str(e)}"

if __name__ == "__main__":
    # This allows running the server directly
    mcp.run()
