import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add backend dir to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import get_supabase
from models import RuleType, _generate_id, BudgetRuleCreate
from services import budget_rule_service

# Load env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

def migrate():
    sb = get_supabase()
    if len(sys.argv) < 2:
        print("Usage: python migrate_rules.py <username>")
        return
    username = sys.argv[1]
    
    # Get user
    users = sb.table("veto_users").select("*").eq("username", username).execute().data
    if not users:
        print("User not found")
        return
    user_id = users[0]["id"]
    print(f"Migrating rules for {username} ({user_id})...")

    # Get existing rules
    rules = sb.table("veto_budget_rules").select("*").eq("user_id", user_id).execute().data
    
    # Check for 50/30/20 rule
    deleted_count = 0
    for rule in rules:
        if rule["rule_type"] == "percentage_allocation" and ("50/30/20" in rule["name"] or "50/30/20" in rule["config"]):
            print(f"Deleting old rule: {rule['name']}")
            budget_rule_service.delete_rule(sb, user_id, rule["id"])
            deleted_count += 1
            
    if deleted_count > 0 or len(rules) == 0:
        print("Creating new 3-part rules...")
        # 1. Needs
        r1 = BudgetRuleCreate(rule_type=RuleType.percentage_needs, name="Needs Limit (50%)", config=json.dumps({"percent": 50}))
        budget_rule_service.create_rule(sb, user_id, r1)
        
        # 2. Wants
        r2 = BudgetRuleCreate(rule_type=RuleType.percentage_wants, name="Wants Limit (30%)", config=json.dumps({"percent": 30}))
        budget_rule_service.create_rule(sb, user_id, r2)
        
        # 3. Savings
        r3 = BudgetRuleCreate(rule_type=RuleType.percentage_allocation, name="Savings Goal (20%)", config=json.dumps({"savings": 20}))
        budget_rule_service.create_rule(sb, user_id, r3)
        
        print("✅ Migration complete. Created 3 rules.")
    else:
        print("No 50/30/20 rule found to migrate.")

if __name__ == "__main__":
    migrate()
