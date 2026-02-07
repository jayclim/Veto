# Veto — Project Guide

## Overview
Veto is an AI-powered personal budgeting app with integrated AI agents. Users log in with a username, track income/expenses, view spending summaries, and chat with an AI assistant that has access to budget data, Capital One (via Nessie), and Visa APIs through MCP (Model Context Protocol).

---

## Architecture

### Frontend — Next.js (TypeScript)
**Port:** `localhost:3000`

| Directory | Purpose |
|-----------|---------|
| `app/` | Next.js pages (dashboard at `/`, budget at `/budget`, cards at `/cards`) |
| `components/layout/` | Shell components: `AppLayout`, `Header`, `Sidebar`, `ChatPanel` |
| `components/` | Standalone components: `LoginScreen` |
| `context/AuthContext.tsx` | Auth state — stores username in `localStorage`, provides `login()`/`logout()` |
| `lib/api.ts` | `apiFetch()` helper — attaches `X-User-Username` header to all backend calls |

### Backend — FastAPI (Python)
**Port:** `localhost:8000`

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, CORS config, router mounting |
| `backend/database.py` | Supabase client initialization |
| `backend/models.py` | Table models (DB) + Public models (Pydantic schemas with camelCase aliases) |
| `backend/auth.py` | `X-User-Username` header — find or create user |
| [VetoMCP](https://github.com/jayclim/VetoMCP) | External MCP Server — exposes budget tools for AI agents (separate repo) |
| `backend/services/agent_service.py` | AI agent with Dedalus Labs integration |
| `backend/services/transaction_service.py` | `add_transaction`, `delete_transaction`, `get_transactions` |
| `backend/services/budget_rule_service.py` | Budget rules management and compliance checking |
| `backend/services/agent_guard_service.py` | Agent guard rails: spending limits, authorization, audit logging |
| `backend/routes/transactions.py` | `POST/GET/DELETE /api/v1/transactions` |
| `backend/routes/budgets.py` | `POST/GET /api/v1/budgets/rules`, `GET /api/v1/budgets/compliance` |
| `backend/routes/chat.py` | `POST /api/v1/chat` — AI assistant endpoint |

---

## Auth Flow
1. User enters a username on the login screen
2. Username is stored in `localStorage` via `AuthContext`
3. Every API call includes the `X-User-Username` header
4. Backend auto-creates the user on first request
5. All data (transactions, budgets, categories) is scoped to the user
6. Logout clears `localStorage` and returns to the login screen

---

## API Endpoints

All routes are prefixed with `/api/v1`. All require the `X-User-Username` header.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/transactions` | Create a transaction |
| `GET` | `/transactions` | List transactions (filters: `category`, `transaction_type`, `start_date`, `end_date`) |
| `DELETE` | `/transactions/{id}` | Delete a transaction |
| `POST` | `/budgets/rules` | Create a budget rule |
| `GET` | `/budgets/rules` | List budget rules |
| `GET` | `/budgets/compliance` | Check budget compliance (income, expenses, net, rule status) |
| `POST` | `/chat` | Send message to AI assistant, returns response with optional actions |

**JSON convention:** Backend uses `snake_case` internally; API responses use `camelCase` (e.g., `transactionType`, `totalIncome`, `createdAt`).

---

## AI Agent Chat

### Overview
The AI chat system (`backend/routes/chat.py` + `backend/services/agent_service.py`) provides a conversational financial assistant powered by Dedalus Labs.

### Endpoint
```
POST /api/v1/chat
```

**Request:**
```json
{
  "message": "What's my spending this month?",
  "conversationHistory": [...]  // Optional prior messages
}
```

**Response:**
```json
{
  "id": "abc123",
  "role": "assistant",
  "content": "Your total spending is $1,234...",
  "timestamp": "2026-02-07T12:00:00Z",
  "actions": [...]  // Executed actions (e.g., transactions added/deleted)
}
```

### Agent Capabilities
The agent receives financial context (dashboard summary, categories, recent transactions) and can execute actions via `[ACTION]...[/ACTION]` blocks:
- `add_transaction` — Record new income/expense
- `delete_transaction` — Remove a transaction by ID

### MCP Tools Available to Agent
Via Dedalus Labs, the agent has access to:
- **VetoMCP** ([jayclim/VetoMCP](https://github.com/jayclim/VetoMCP)) — Budget management tools (external repo)
- **NessieMCP** (`tpparikh/abc`) — Capital One sandbox API
- **VisaMCP** (`tpparikh/-visaMCP`) — Visa APIs (limited access)

---

## VetoMCP (External Repository)

**Repository:** [github.com/jayclim/VetoMCP](https://github.com/jayclim/VetoMCP)

The Veto MCP Server is maintained in a separate repository and exposes budget tools for AI agents via the Model Context Protocol.

### Server Tools (Require Database)

| Tool | Description |
|------|-------------|
| `add_transaction` | Record a new financial transaction (expense or income) |
| `delete_transaction` | Delete a transaction by ID |
| `get_transactions` | List recent transactions with optional filtering |
| `get_dashboard_summary` | Get financial summary (income, expenses, net, category breakdown) |
| `create_budget_rule` | Create budget rule (percentage_allocation, category_limit, savings_goal, spending_alert) |
| `get_budget_rules` | List all active budget rules |
| `delete_budget_rule` | Delete a budget rule by ID |
| `check_rule_compliance` | Check if user is following their active budget rules |
| `get_spending_insights` | Get AI-friendly spending insights and patterns |

### Local Tools (No Database Access)

| Tool | Description |
|------|-------------|
| `get_budget_methods` | Returns popular budget methods (50/30/20, Zero-Based, Envelope, etc.) |
| `check_budget_for_purchase` | Check if a purchase is within budget (returns APPROVE/CAUTION/DENY) |
| `suggest_budget_allocation` | Suggest budget allocations based on income and method |
| `get_budget_health_score` | Calculate 0-100 financial health score with grade (A-F) |
| `project_monthly_spending` | Project end-of-month spending based on current pace |

### Agent Guard Rails (For External Autonomous Agents)

These tools enable external autonomous agents to check budget compliance **before** making purchases on behalf of users. They are advisory tools that help prevent agents from overspending.

**Local Tools (No Database):**

| Tool | Description |
|------|-------------|
| `authorize_purchase` | **Primary tool** — Check if purchase is authorized (returns APPROVED/DENIED/CAUTION/REQUIRES_HUMAN_APPROVAL) |
| `get_agent_spending_limits` | Get configured spending limits for agents (daily, weekly, monthly, per-transaction) |
| `assess_purchase_risk` | Calculate risk score (0-100) with risk factors and recommendation |
| `validate_agent_action` | Validate any agent action type (purchase, transfer, subscription, recurring_payment) |

**Database-Backed Tools:**

| Tool | Description |
|------|-------------|
| `set_agent_spending_limits` | Configure user's spending limits for agents |
| `get_agent_settings` | Get all agent settings including category restrictions |
| `log_agent_authorization` | Log authorization attempts for audit trail |
| `get_agent_authorization_history` | View past authorization attempts |
| `get_cumulative_agent_spend` | Get cumulative agent spending by period (daily/weekly/monthly) |

**Example Flow for External Agent:**
```
1. Agent calls get_agent_spending_limits(username) to understand limits
2. Agent calls authorize_purchase(username, amount, category, merchant)
3. VetoMCP returns: { "status": "APPROVED", "budget_remaining": 250.00 }
4. Agent proceeds with purchase via Nessie/Visa
5. Agent calls log_agent_authorization(...) to record the action
```

### Running the MCP Server
See the [VetoMCP README](https://github.com/jayclim/VetoMCP) for setup and running instructions.

---

## External MCPs (via Dedalus Labs)

### NessieMCP (`tpparikh/abc`)
Capital One Nessie sandbox API for banking simulation.

**Available Tools:**
- **Accounts:** `get_all_accounts`, `get_account`, `get_accounts_by_customer`, `create_account`, `update_account`, `delete_account`
- **Customers:** `get_all_customers`, `get_customer`, `get_customers_by_account`, `create_customer`, `update_customer`
- **Transactions:** `get_all_transactions`, `get_transaction`, `create_deposit`, `create_withdrawal`, `delete_deposit`, `delete_withdrawal`
- **Purchases:** `get_all_purchases`, `get_purchase`, `get_purchases_by_account`, `get_purchases_by_merchant`, `create_purchase`, `update_purchase`, `delete_purchase`
- **Transfers:** `get_all_transfers`, `get_transfer`, `create_transfer`, `update_transfer`, `delete_transfer`
- **Bills:** `get_all_bills`, `get_bill`, `get_bills_by_account`, `get_bills_by_customer`, `create_bill`, `update_bill`, `delete_bill`
- **Merchants:** `get_all_merchants`, `get_merchant`, `get_merchants_by_location`, `create_merchant`, `update_merchant`
- **ATMs/Branches:** `get_all_atms`, `get_atm`, `get_atms_by_location`, `get_all_branches`, `get_branch`

### VisaMCP (`tpparikh/-visaMCP`)
Visa APIs (limited access due to sandbox restrictions).

**Available Tools:**
- `find_nearby_offers` — Find Visa offers near a location
- `find_nearby_atms` — Find Visa ATMs

*Note: Most Visa tools are restricted. Use Nessie data to mock credit card features.*

---

## Seeding Scripts

### `backend/scripts/seed_nessie.py`
Seeds both Supabase and Nessie sandbox with realistic financial data.

**Usage:**
```bash
cd backend/scripts
python seed_nessie.py <username>  # Username is required
```

**What it seeds:**

**Supabase:**
- Creates/finds user by username
- Clears existing data for the user
- Creates 7 budget rules (Housing, Food, Transport, etc. + Savings Goal)
- Creates 15 sample transactions spanning the last week

**Nessie (via Dedalus Labs):**
- Creates customer with the username
- Creates merchant "Capital One Cafe"
- Creates two accounts: "Capital One 360 Checking" and "Visa Infinite" (credit card)
- Creates initial $5,000 salary deposit
- Creates sample Visa purchase at Capital One Cafe
- Creates $500 transfer (credit card payment)

**Environment Variables Required:**
- `DEDALUS_API_KEY` — Dedalus Labs API key
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key

---

## Veto AI Chat Panel

The right-side chat panel (`components/layout/ChatPanel.tsx`) provides a conversational interface for financial insights.

- **Identity:** Veto AI, with gradient avatar and pulsing online indicator
- **Message types:** Text messages and rich content (React nodes embedded in bubbles)
- **User avatar:** Derived from the authenticated username initial
- **State:** Toggle visibility via the header smart_toy icon button
- **Backend:** Connects to `/api/v1/chat` endpoint

---

## Running Locally

```bash
# Backend
cd backend && pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000

# Frontend
npm install && npm run dev

# Seed data (optional)
cd backend/scripts && python seed_nessie.py [username]
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DEDALUS_API_KEY=your-dedalus-api-key
```

---

## Key Design Decisions
- **Supabase** for managed PostgreSQL — all tables use `veto_` prefix: `veto_users`, `veto_transactions`, `veto_budget_rules`, `veto_agent_settings`, `veto_agent_authorization_log`
- **Header-based auth** (`X-User-Username`) — simple, no tokens, hackathon-friendly
- **Service layer pattern** — routes are thin wrappers, logic is testable and MCP-portable
- **camelCase aliases** on Pydantic models so the frontend gets idiomatic JSON without manual conversion
- **MCP-first design** — all budget logic exposed as MCP tools for AI agent consumption
- **Dedalus Labs integration** — enables multi-MCP orchestration (Veto + Nessie + Visa)
