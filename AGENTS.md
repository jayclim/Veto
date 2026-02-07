# Veto — Project Guide

## Overview
Veto is an AI-powered personal budgeting app. Users log in with a username, track income/expenses, and view spending summaries broken down by category.

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
| `backend/database.py` | SQLite via SQLModel, session dependency |
| `backend/models.py` | Table models (DB) + Public models (Pydantic schemas with camelCase aliases) |
| `backend/auth.py` | `X-User-Username` header — find or create user |
| `backend/services/transaction_service.py` | `add_transaction`, `delete_transaction`, `get_transactions` |
| `backend/services/budget_service.py` | `create_category`, `get_categories`, `get_dashboard_summary` |
| `backend/routes/transactions.py` | `POST/GET/DELETE /api/v1/transactions` |
| `backend/routes/budgets.py` | `POST/GET /api/v1/budgets/categories`, `GET /api/v1/budgets/dashboard` |

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
| `POST` | `/budgets/categories` | Create a budget category |
| `GET` | `/budgets/categories` | List budget categories |
| `GET` | `/budgets/dashboard` | Dashboard summary (income, expenses, net, per-category breakdown) |

**JSON convention:** Backend uses `snake_case` internally; API responses use `camelCase` (e.g., `transactionType`, `totalIncome`, `createdAt`).

---

## Veto AI Chat Panel

The right-side chat panel (`ChatPanel.tsx`) provides a conversational interface for financial insights.

- **Identity:** Veto AI, with gradient avatar and pulsing online indicator
- **Message types:** Text messages and rich content (React nodes embedded in bubbles)
- **User avatar:** Derived from the authenticated username initial
- **State:** Toggle visibility via the header smart_toy icon button

---

## MCP Readiness
All business logic lives in `backend/services/` as standalone, typed functions with docstrings. The API routes contain no logic — they only call service functions. This makes it straightforward to expose the same logic as an MCP Server via Dedalus Labs.

---

## Running Locally

```bash
# Backend
cd backend && pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000

# Frontend
npm install && npm run dev
```

---

## Key Design Decisions
- **SQLite + SQLModel** for zero-config persistence with Pydantic integration
- **Header-based auth** (`X-User-Username`) — simple, no tokens, hackathon-friendly
- **Service layer pattern** — routes are thin wrappers, logic is testable and MCP-portable
- **camelCase aliases** on Pydantic models so the frontend gets idiomatic JSON without manual conversion
