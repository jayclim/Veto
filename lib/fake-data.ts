// ─── Fake seed data ───────────────────────────────────────────────
// Structured to match the exact shapes consumed by all pages.
// When real data is ready, flip USE_FAKE_DATA in lib/api.ts to false.

export interface Transaction {
  id: string;
  amount: number;
  description: string;
  category: string;
  transactionType: "income" | "expense";
  date: string;
  createdAt: string;
}

export interface CategorySummary {
  category: string;
  totalSpent: number;
  budgetLimit: number | null;
  remaining: number | null;
}

export interface DashboardSummary {
  totalIncome: number;
  totalExpenses: number;
  net: number;
  categories: CategorySummary[];
}

// ─── Transactions ─────────────────────────────────────────────────

export const FAKE_TRANSACTIONS: Transaction[] = [
  // Income
  {
    id: "tx-001",
    amount: 4250.0,
    description: "Salary Deposit",
    category: "Income",
    transactionType: "income",
    date: "2026-02-01T09:00:00Z",
    createdAt: "2026-02-01T09:00:00Z",
  },
  {
    id: "tx-002",
    amount: 320.0,
    description: "Freelance Design Work",
    category: "Income",
    transactionType: "income",
    date: "2026-02-03T14:30:00Z",
    createdAt: "2026-02-03T14:30:00Z",
  },
  {
    id: "tx-003",
    amount: 75.0,
    description: "Sold Textbooks",
    category: "Income",
    transactionType: "income",
    date: "2026-01-28T11:00:00Z",
    createdAt: "2026-01-28T11:00:00Z",
  },

  // Food & Dining
  {
    id: "tx-010",
    amount: 42.5,
    description: "Whole Foods Groceries",
    category: "Food & Dining",
    transactionType: "expense",
    date: "2026-02-06T18:20:00Z",
    createdAt: "2026-02-06T18:20:00Z",
  },
  {
    id: "tx-011",
    amount: 15.75,
    description: "Chipotle Lunch",
    category: "Food & Dining",
    transactionType: "expense",
    date: "2026-02-05T12:30:00Z",
    createdAt: "2026-02-05T12:30:00Z",
  },
  {
    id: "tx-012",
    amount: 68.0,
    description: "Dinner at Olive Garden",
    category: "Food & Dining",
    transactionType: "expense",
    date: "2026-02-02T20:15:00Z",
    createdAt: "2026-02-02T20:15:00Z",
  },
  {
    id: "tx-013",
    amount: 5.5,
    description: "Morning Coffee",
    category: "Food & Dining",
    transactionType: "expense",
    date: "2026-02-07T07:45:00Z",
    createdAt: "2026-02-07T07:45:00Z",
  },

  // Housing
  {
    id: "tx-020",
    amount: 1450.0,
    description: "February Rent",
    category: "Housing",
    transactionType: "expense",
    date: "2026-02-01T00:00:00Z",
    createdAt: "2026-02-01T00:00:00Z",
  },
  {
    id: "tx-021",
    amount: 85.0,
    description: "Renters Insurance",
    category: "Housing",
    transactionType: "expense",
    date: "2026-02-01T00:00:00Z",
    createdAt: "2026-02-01T00:00:00Z",
  },

  // Transportation
  {
    id: "tx-030",
    amount: 48.0,
    description: "Gas Station Fill-up",
    category: "Transportation",
    transactionType: "expense",
    date: "2026-02-04T16:00:00Z",
    createdAt: "2026-02-04T16:00:00Z",
  },
  {
    id: "tx-031",
    amount: 12.5,
    description: "Uber to Downtown",
    category: "Transportation",
    transactionType: "expense",
    date: "2026-02-06T21:30:00Z",
    createdAt: "2026-02-06T21:30:00Z",
  },

  // Entertainment (over budget — limit $100, spending ~$142)
  {
    id: "tx-040",
    amount: 16.99,
    description: "Movie Tickets",
    category: "Entertainment",
    transactionType: "expense",
    date: "2026-02-05T19:00:00Z",
    createdAt: "2026-02-05T19:00:00Z",
  },
  {
    id: "tx-041",
    amount: 65.0,
    description: "Concert Tickets",
    category: "Entertainment",
    transactionType: "expense",
    date: "2026-02-03T10:00:00Z",
    createdAt: "2026-02-03T10:00:00Z",
  },
  {
    id: "tx-042",
    amount: 34.99,
    description: "Bowling Night",
    category: "Entertainment",
    transactionType: "expense",
    date: "2026-02-06T20:00:00Z",
    createdAt: "2026-02-06T20:00:00Z",
  },
  {
    id: "tx-043",
    amount: 24.99,
    description: "Arcade Bar",
    category: "Entertainment",
    transactionType: "expense",
    date: "2026-02-07T18:30:00Z",
    createdAt: "2026-02-07T18:30:00Z",
  },

  // Shopping (over budget — limit $150, spending ~$265)
  {
    id: "tx-050",
    amount: 89.99,
    description: "Nike Running Shoes",
    category: "Shopping",
    transactionType: "expense",
    date: "2026-02-04T14:00:00Z",
    createdAt: "2026-02-04T14:00:00Z",
  },
  {
    id: "tx-051",
    amount: 24.99,
    description: "Amazon — Phone Case",
    category: "Shopping",
    transactionType: "expense",
    date: "2026-02-06T09:15:00Z",
    createdAt: "2026-02-06T09:15:00Z",
  },
  {
    id: "tx-052",
    amount: 119.0,
    description: "Target — Home Decor",
    category: "Shopping",
    transactionType: "expense",
    date: "2026-02-05T15:00:00Z",
    createdAt: "2026-02-05T15:00:00Z",
  },
  {
    id: "tx-053",
    amount: 31.5,
    description: "Amazon — USB Hub",
    category: "Shopping",
    transactionType: "expense",
    date: "2026-02-07T10:00:00Z",
    createdAt: "2026-02-07T10:00:00Z",
  },

  // Subscriptions
  {
    id: "tx-060",
    amount: 15.99,
    description: "Netflix Premium",
    category: "Subscriptions",
    transactionType: "expense",
    date: "2026-02-01T00:00:00Z",
    createdAt: "2026-02-01T00:00:00Z",
  },
  {
    id: "tx-061",
    amount: 10.99,
    description: "Spotify Family",
    category: "Subscriptions",
    transactionType: "expense",
    date: "2026-02-01T00:00:00Z",
    createdAt: "2026-02-01T00:00:00Z",
  },
  {
    id: "tx-062",
    amount: 14.99,
    description: "iCloud+ Storage",
    category: "Subscriptions",
    transactionType: "expense",
    date: "2026-02-01T00:00:00Z",
    createdAt: "2026-02-01T00:00:00Z",
  },

  // Health
  {
    id: "tx-070",
    amount: 45.0,
    description: "Gym Membership",
    category: "Health",
    transactionType: "expense",
    date: "2026-02-01T00:00:00Z",
    createdAt: "2026-02-01T00:00:00Z",
  },

  // Utilities
  {
    id: "tx-080",
    amount: 120.0,
    description: "Electric Bill",
    category: "Utilities",
    transactionType: "expense",
    date: "2026-02-03T00:00:00Z",
    createdAt: "2026-02-03T00:00:00Z",
  },
  {
    id: "tx-081",
    amount: 65.0,
    description: "Internet — Xfinity",
    category: "Utilities",
    transactionType: "expense",
    date: "2026-02-03T00:00:00Z",
    createdAt: "2026-02-03T00:00:00Z",
  },

  // Savings
  {
    id: "tx-090",
    amount: 200.0,
    description: "Monthly Savings Transfer",
    category: "Savings",
    transactionType: "expense",
    date: "2026-02-01T10:00:00Z",
    createdAt: "2026-02-01T10:00:00Z",
  },
];

// ─── Dashboard summary (derived from transactions) ────────────────

function buildDashboard(txs: Transaction[]): DashboardSummary {
  const totalIncome = txs
    .filter((t) => t.transactionType === "income")
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpenses = txs
    .filter((t) => t.transactionType === "expense")
    .reduce((sum, t) => sum + t.amount, 0);

  // Budget limits per category (simulate what the backend would return)
  // Only a few categories have budgets set — the rest can be added via the UI
  const budgetLimits: Record<string, number> = {
    "Food & Dining": 400,
    Entertainment: 100,
    Shopping: 150,
  };

  const categoryTotals = new Map<string, number>();
  for (const tx of txs) {
    if (tx.transactionType === "expense") {
      categoryTotals.set(
        tx.category,
        (categoryTotals.get(tx.category) ?? 0) + tx.amount
      );
    }
  }

  const categories: CategorySummary[] = Array.from(categoryTotals.entries())
    .map(([category, totalSpent]) => {
      const limit = budgetLimits[category] ?? null;
      return {
        category,
        totalSpent,
        budgetLimit: limit,
        remaining: limit !== null ? limit - totalSpent : null,
      };
    })
    .sort((a, b) => b.totalSpent - a.totalSpent);

  return {
    totalIncome,
    totalExpenses,
    net: totalIncome - totalExpenses,
    categories,
  };
}

export const FAKE_DASHBOARD: DashboardSummary =
  buildDashboard(FAKE_TRANSACTIONS);
