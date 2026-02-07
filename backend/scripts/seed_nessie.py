import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from dedalus_labs import AsyncDedalus, DedalusRunner
from supabase import create_client

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
DEDALUS_API_KEY = os.environ.get("DEDALUS_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

MCP_SERVER = "tpparikh/abc"

# Seed data definitions (shared between Nessie and Supabase)
BUDGET_RULES = [
    {
        "name": "50/30/20 Allocation",
        "rule_type": "percentage_allocation",
        "config": '{"needs": 50, "wants": 30, "savings": 20}'
    }
]

TRANSACTIONS = [
    {"amount": 5000, "description": "Salary - Capital One Direct Deposit", "category": "Income", "type": "income", "days_ago": 6},
    {"amount": 1350, "description": "Rent Payment", "category": "Housing", "type": "expense", "days_ago": 6},
    {"amount": 45.99, "description": "Whole Foods Groceries", "category": "Food & Dining", "type": "expense", "days_ago": 5},
    {"amount": 12.50, "description": "Capital One Cafe - Visa", "category": "Food & Dining", "type": "expense", "days_ago": 5},
    {"amount": 55.00, "description": "Gas Station - Shell", "category": "Transportation", "type": "expense", "days_ago": 4},
    {"amount": 14.99, "description": "Netflix Subscription", "category": "Entertainment", "type": "expense", "days_ago": 4},
    {"amount": 89.99, "description": "Amazon - Electronics", "category": "Shopping", "type": "expense", "days_ago": 3},
    {"amount": 120.00, "description": "Electric Bill", "category": "Utilities", "type": "expense", "days_ago": 3},
    {"amount": 65.00, "description": "Internet - Comcast", "category": "Utilities", "type": "expense", "days_ago": 3},
    {"amount": 32.75, "description": "Uber Ride", "category": "Transportation", "type": "expense", "days_ago": 2},
    {"amount": 78.50, "description": "Dinner - Olive Garden (Visa)", "category": "Food & Dining", "type": "expense", "days_ago": 2},
    {"amount": 250.00, "description": "Freelance Payment", "category": "Income", "type": "income", "days_ago": 2},
    {"amount": 9.99, "description": "Spotify Premium", "category": "Entertainment", "type": "expense", "days_ago": 1},
    {"amount": 42.30, "description": "Target - Household Items", "category": "Shopping", "type": "expense", "days_ago": 1},
    {"amount": 28.00, "description": "Chipotle - Visa", "category": "Food & Dining", "type": "expense", "days_ago": 0},
]


def seed_supabase(username: str):
    """Seed the Supabase database with user, budget rules, and transactions."""
    print("\n📦 Seeding Supabase database...")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Find or create user
    result = sb.table("veto_users").select("*").eq("username", username).execute()
    if result.data:
        user_id = result.data[0]["id"]
        print(f"  Found existing user: {username} ({user_id})")
    else:
        user_id = uuid4().hex
        sb.table("veto_users").insert({"id": user_id, "username": username}).execute()
        print(f"  Created user: {username} ({user_id})")

    # Clear existing data for this user
    sb.table("veto_budget_rules").delete().eq("user_id", user_id).execute()
    sb.table("veto_transactions").delete().eq("user_id", user_id).execute()
    print("  Cleared existing data.")

    # Insert budget rules
    rule_rows = [
        {
            "id": uuid4().hex,
            "user_id": user_id,
            "name": r["name"],
            "rule_type": r["rule_type"],
            "config": r["config"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for r in BUDGET_RULES
    ]
    sb.table("veto_budget_rules").insert(rule_rows).execute()
    print(f"  Created {len(rule_rows)} budget rules.")

    # Insert transactions
    now = datetime.now(timezone.utc)
    tx_rows = [
        {
            "id": uuid4().hex,
            "user_id": user_id,
            "amount": t["amount"],
            "description": t["description"],
            "category": t["category"],
            "transaction_type": t["type"],
            "date": (now - timedelta(days=t["days_ago"])).isoformat(),
        }
        for t in TRANSACTIONS
    ]
    sb.table("veto_transactions").insert(tx_rows).execute()
    print(f"  Created {len(tx_rows)} transactions.")
    print("✅ Supabase seeding complete.")


async def seed_nessie(username: str):
    """Seed the Nessie sandbox with customer, accounts, and transactions."""
    print("\n🏦 Seeding Nessie (Capital One + Visa)...")
    client = AsyncDedalus(api_key=DEDALUS_API_KEY)
    runner = DedalusRunner(client)

    async def run_step(step_name, prompt):
        print(f"  👉 {step_name}...")
        try:
            result = await runner.run(
                model="gpt-5.2",
                input=prompt,
                mcp_servers=[MCP_SERVER],
            )
            print(f"  ✅ {step_name} complete.")
            return result.content
        except Exception as e:
            print(f"  ❌ {step_name} failed: {e}")
            return None

    await run_step("Customer Setup", f"""
    Check if a customer named "{username}" exists.
    If not, create one: {username}, 123 Innovation Dr, McLean, VA 22102.
    IMPORTANT: Return the Customer ID of "{username}" clearly in your response.
    """)

    await run_step("Merchant Setup", """
    Create a merchant named "Capital One Cafe" if it doesn't already exist.
    Use these parameters:
    - name: "Capital One Cafe"
    - category: "Dining"
    - street_number: "1680"
    - street_name: "Capital One Drive"
    - city: "McLean"
    - state: "VA"
    - zip_code: "22102"
    - latitude: 38.9247
    - longitude: -77.2134
    """)

    await run_step("Account Setup", f"""
    Find the customer "{username}".
    Ensure they have these two accounts:
    1. "Capital One 360 Checking" (Type: Checking, Rewards: 0, Balance: 0)
    2. "Visa Infinite" (Type: Credit Card, Rewards: 0, Balance: 0)
    If they don't exist, create them.
    """)

    await run_step("Initial Deposit", f"""
    Find the "Capital One 360 Checking" account for "{username}".
    Create a deposit of $5000 (medium: balance) description: "Salary".
    """)

    await run_step("Visa Spending", f"""
    1. Find the "Visa Infinite" account for "{username}".
    2. Find the merchant "Capital One Cafe".
    3. Create a purchase of $12.50 at that merchant for this account.
    """)

    await run_step("Bill Payment", f"""
    Find "{username}".
    Create a transfer of $500 from their "Capital One 360 Checking" to their "Visa Infinite" account.
    """)

    print("✅ Nessie seeding complete.")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python seed_nessie.py <username>")
        return
    username = sys.argv[1]

    print(f"🌱 Seeding data for user: {username}")

    # Seed both in parallel
    seed_supabase(username)
    await seed_nessie(username)

    print(f"\n🎉 All seeding complete for '{username}'!")


if __name__ == "__main__":
    asyncio.run(main())