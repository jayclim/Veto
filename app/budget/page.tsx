'use client';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiFetch } from '@/lib/api';
import { CATEGORIES, getCategoryStyle } from '@/lib/categories';

interface Transaction {
    id: string;
    amount: number;
    description: string;
    category: string;
    transactionType: 'income' | 'expense';
    date: string;
}

interface BudgetCategory {
    id: string;
    name: string;
    monthlyLimit: number;
    createdAt: string;
}

interface CategorySummary {
    category: string;
    totalSpent: number;
    budgetLimit: number | null;
    remaining: number | null;
}

interface DashboardSummary {
    totalIncome: number;
    totalExpenses: number;
    net: number;
    categories: CategorySummary[];
}

function fmt(n: number): string {
    return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

function fmtDate(iso: string): string {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function getStyle(name: string) {
    return getCategoryStyle(name);
}

export default function BudgetPage() {
    const { username } = useAuth();
    const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);

    // Add category form
    const [showAddCat, setShowAddCat] = useState(false);
    const [catName, setCatName] = useState(CATEGORIES[0].name);
    const [catLimit, setCatLimit] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const refresh = useCallback(async () => {
        if (!username) return;
        try {
            const [dash, txs] = await Promise.all([
                apiFetch<DashboardSummary>('/budgets/dashboard', {}, username),
                apiFetch<Transaction[]>('/transactions', {}, username),
            ]);
            setDashboard(dash);
            setTransactions(txs);
        } catch (e) {
            console.error('Failed to fetch budget data:', e);
        } finally {
            setLoading(false);
        }
    }, [username]);

    useEffect(() => { refresh(); }, [refresh]);

    const handleAddCategory = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!username || !catName.trim() || !catLimit) return;
        setSubmitting(true);
        try {
            await apiFetch('/budgets/categories', {
                method: 'POST',
                body: JSON.stringify({ name: catName.trim(), monthly_limit: parseFloat(catLimit) }),
            }, username);
            setCatName(CATEGORIES[0].name);
            setCatLimit('');
            setShowAddCat(false);
            await refresh();
        } catch (e) {
            console.error('Failed to add category:', e);
        } finally {
            setSubmitting(false);
        }
    };

    const now = new Date();
    const monthLabel = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

    const totalBudget = dashboard?.categories.reduce((sum, c) => sum + (c.budgetLimit ?? 0), 0) ?? 0;
    const totalSpent = dashboard?.totalExpenses ?? 0;
    const budgetPct = totalBudget > 0 ? Math.min(Math.round((totalSpent / totalBudget) * 100), 100) : 0;

    // Recent expense transactions (last 5)
    const recentExpenses = transactions.filter(t => t.transactionType === 'expense').slice(0, 5);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="flex gap-1 items-center">
                    <div className="size-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0s' }}></div>
                    <div className="size-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                    <div className="size-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0.3s' }}></div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-white text-2xl font-bold tracking-tight">Budget Analysis</h2>
                    <p className="text-slate-400 text-sm">{monthLabel} Overview</p>
                </div>
                <button
                    onClick={() => setShowAddCat(!showAddCat)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-all"
                >
                    <span className="material-symbols-outlined text-[18px]">{showAddCat ? 'close' : 'add'}</span>
                    {showAddCat ? 'Cancel' : 'Add Budget Category'}
                </button>
            </div>

            {/* Add Category Form */}
            {showAddCat && (
                <div className="glass-panel rounded-2xl p-6">
                    <h3 className="text-white font-semibold mb-4">New Budget Category</h3>
                    <form onSubmit={handleAddCategory} className="flex flex-col sm:flex-row gap-4 items-end">
                        <div className="flex flex-col gap-1 flex-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider">Category</label>
                            <select
                                value={catName}
                                onChange={(e) => setCatName(e.target.value)}
                                className="px-3 py-2.5 rounded-lg bg-slate-900/50 border border-slate-800 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm appearance-none"
                            >
                                {CATEGORIES.map((c) => (
                                    <option key={c.name} value={c.name}>{c.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="flex flex-col gap-1 flex-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider">Monthly Limit</label>
                            <input
                                type="number"
                                step="0.01"
                                min="1"
                                value={catLimit}
                                onChange={(e) => setCatLimit(e.target.value)}
                                placeholder="500.00"
                                required
                                className="px-3 py-2.5 rounded-lg bg-slate-900/50 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm font-mono"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="px-6 py-2.5 rounded-lg bg-primary hover:bg-blue-600 disabled:opacity-40 text-white text-sm font-semibold transition-colors"
                        >
                            {submitting ? 'Adding...' : 'Add'}
                        </button>
                    </form>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    {/* Monthly Spend vs Budget */}
                    <div className="glass-panel rounded-2xl p-6 relative overflow-hidden group">
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-primary/5 blur-[80px] rounded-full pointer-events-none"></div>
                        <div className="relative z-10">
                            <h3 className="text-white text-lg font-semibold flex items-center gap-2 mb-1">
                                <span className="material-symbols-outlined text-primary">analytics</span>
                                Monthly Spend vs Budget
                            </h3>
                            <div className="flex items-baseline gap-2 mb-6">
                                <span className="text-3xl font-bold text-white font-mono tracking-tight">{fmt(totalSpent)}</span>
                                {totalBudget > 0 && <span className="text-slate-500 text-sm font-mono">/ {fmt(totalBudget)}</span>}
                            </div>

                            {totalBudget > 0 ? (
                                <div className="mb-2">
                                    <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all ${budgetPct >= 90 ? 'bg-crimson-accent' : budgetPct >= 70 ? 'bg-yellow-500' : 'bg-primary'}`}
                                            style={{ width: `${budgetPct}%` }}
                                        ></div>
                                    </div>
                                    <p className="text-xs text-slate-500 mt-2 text-right">{budgetPct}% of total budget used</p>
                                </div>
                            ) : (
                                <p className="text-slate-500 text-sm">Add budget categories to track spending limits</p>
                            )}
                        </div>
                    </div>

                    {/* Category Cards */}
                    {dashboard && dashboard.categories.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {dashboard.categories.map((cat) => {
                                const style = getStyle(cat.category);
                                const pct = cat.budgetLimit && cat.budgetLimit > 0
                                    ? Math.min(Math.round((cat.totalSpent / cat.budgetLimit) * 100), 100)
                                    : null;
                                return (
                                    <div key={cat.category} className={`glass-panel p-5 rounded-2xl border-l-4 ${style.border} hover:translate-y-[-2px] transition-transform duration-300`}>
                                        <div className="flex justify-between items-start mb-4">
                                            <div className={`p-2 rounded-lg ${style.bg} ${style.color}`}>
                                                <span className="material-symbols-outlined">{style.icon}</span>
                                            </div>
                                            {pct !== null && (
                                                <span className={`text-xs font-mono ${style.color} ${style.bg} px-2 py-1 rounded-full`}>{pct}%</span>
                                            )}
                                        </div>
                                        <h4 className="text-slate-300 text-sm font-medium mb-1">{cat.category}</h4>
                                        <div className="flex items-baseline gap-1 mb-3">
                                            <span className="text-white text-xl font-bold font-mono">{fmt(cat.totalSpent)}</span>
                                            {cat.budgetLimit !== null && (
                                                <span className="text-slate-500 text-xs font-mono">/ {fmt(cat.budgetLimit)}</span>
                                            )}
                                        </div>
                                        {pct !== null && (
                                            <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full transition-all ${pct >= 90 ? 'bg-crimson-accent' : pct >= 70 ? 'bg-yellow-500' : 'bg-primary'}`}
                                                    style={{ width: `${pct}%` }}
                                                ></div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Recent Activity */}
                    <div className="glass-panel rounded-2xl p-6">
                        <h3 className="text-white text-lg font-semibold mb-4">Recent Expenses</h3>
                        {recentExpenses.length > 0 ? (
                            <div className="space-y-3">
                                {recentExpenses.map((tx) => {
                                    const style = getStyle(tx.category);
                                    return (
                                        <div key={tx.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors border border-transparent hover:border-white/5">
                                            <div className="flex items-center gap-4">
                                                <div className={`w-10 h-10 rounded-full ${style.bg} flex items-center justify-center ${style.color}`}>
                                                    <span className="material-symbols-outlined text-[20px]">{style.icon}</span>
                                                </div>
                                                <div>
                                                    <p className="text-white font-medium text-sm">{tx.description}</p>
                                                    <p className="text-slate-500 text-xs">{fmtDate(tx.date)} &middot; {tx.category}</p>
                                                </div>
                                            </div>
                                            <span className="text-white font-mono font-medium">-{fmt(tx.amount)}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <p className="text-slate-500 text-sm">No expenses recorded yet</p>
                        )}
                    </div>
                </div>

                {/* Right Column */}
                <div className="flex flex-col gap-6">
                    {/* Total Available Balance */}
                    <div className="glass-panel rounded-2xl p-6 bg-gradient-to-br from-slate-900/80 to-black">
                        <p className="text-slate-400 text-sm font-medium mb-2">Net Balance</p>
                        <h2
                            className={`text-4xl font-bold font-mono tracking-tighter mb-4 ${(dashboard?.net ?? 0) >= 0 ? 'text-white' : 'text-crimson-accent'}`}
                            style={{ textShadow: '0 0 10px rgba(36, 99, 235, 0.3)' }}
                        >
                            {fmt(dashboard?.net ?? 0)}
                        </h2>
                        <div className="grid grid-cols-2 gap-3 text-center">
                            <div className="p-3 rounded-lg bg-emerald-accent/5 border border-emerald-accent/10">
                                <p className="text-emerald-accent text-lg font-bold font-mono">{fmt(dashboard?.totalIncome ?? 0)}</p>
                                <p className="text-slate-500 text-xs">Income</p>
                            </div>
                            <div className="p-3 rounded-lg bg-crimson-accent/5 border border-crimson-accent/10">
                                <p className="text-crimson-accent text-lg font-bold font-mono">{fmt(dashboard?.totalExpenses ?? 0)}</p>
                                <p className="text-slate-500 text-xs">Expenses</p>
                            </div>
                        </div>
                    </div>

                    {/* Budget Categories List */}
                    <div className="glass-panel rounded-2xl p-6">
                        <h3 className="text-white font-semibold mb-4">Budget Limits</h3>
                        {dashboard && dashboard.categories.filter(c => c.budgetLimit !== null).length > 0 ? (
                            <div className="space-y-4">
                                {dashboard.categories.filter(c => c.budgetLimit !== null).map((cat) => {
                                    const pct = cat.budgetLimit! > 0 ? Math.min(Math.round((cat.totalSpent / cat.budgetLimit!) * 100), 100) : 0;
                                    return (
                                        <div key={cat.category} className="flex flex-col gap-2">
                                            <div className="flex justify-between text-sm">
                                                <span className="text-slate-300">{cat.category}</span>
                                                <span className={`font-mono text-xs ${cat.remaining !== null && cat.remaining < 0 ? 'text-crimson-accent' : 'text-emerald-accent'}`}>
                                                    {cat.remaining !== null ? (cat.remaining >= 0 ? `${fmt(cat.remaining)} left` : `${fmt(Math.abs(cat.remaining))} over`) : ''}
                                                </span>
                                            </div>
                                            <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full transition-all ${pct >= 90 ? 'bg-crimson-accent' : pct >= 70 ? 'bg-yellow-500' : 'bg-primary'}`}
                                                    style={{ width: `${pct}%` }}
                                                ></div>
                                            </div>
                                            <div className="flex justify-between text-xs text-slate-500 font-mono">
                                                <span>{fmt(cat.totalSpent)}</span>
                                                <span>{fmt(cat.budgetLimit!)}</span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <p className="text-slate-500 text-sm">No budget limits set. Add a category above to start tracking.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
