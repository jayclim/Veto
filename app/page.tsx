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

export default function DashboardPage() {
    const { username } = useAuth();
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);

    // Form state
    const [formDesc, setFormDesc] = useState('');
    const [formAmount, setFormAmount] = useState('');
    const [formCategory, setFormCategory] = useState(CATEGORIES[0].name);
    const [formType, setFormType] = useState<'income' | 'expense'>('expense');
    const [submitting, setSubmitting] = useState(false);

    const refresh = useCallback(async () => {
        if (!username) return;
        try {
            const [txs, dash] = await Promise.all([
                apiFetch<Transaction[]>('/transactions', {}, username),
                apiFetch<DashboardSummary>('/budgets/dashboard', {}, username),
            ]);
            setTransactions(txs);
            setDashboard(dash);
        } catch (e) {
            console.error('Failed to fetch data:', e);
        } finally {
            setLoading(false);
        }
    }, [username]);

    useEffect(() => {
        refresh();
    }, [refresh]);

    // Listen for AI agent actions that require data refresh
    useEffect(() => {
        const handleDataRefresh = () => {
            refresh();
        };
        window.addEventListener('veto-data-refresh', handleDataRefresh);
        return () => {
            window.removeEventListener('veto-data-refresh', handleDataRefresh);
        };
    }, [refresh]);

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!username || !formDesc.trim() || !formAmount) return;
        setSubmitting(true);
        try {
            await apiFetch('/transactions', {
                method: 'POST',
                body: JSON.stringify({
                    description: formDesc.trim(),
                    amount: parseFloat(formAmount),
                    category: formCategory,
                    transaction_type: formType,
                }),
            }, username);
            setFormDesc('');
            setFormAmount('');
            setFormCategory(CATEGORIES[0].name);
            setFormType('expense');
            setShowForm(false);
            await refresh();
        } catch (e) {
            console.error('Failed to add transaction:', e);
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!username) return;
        try {
            await apiFetch(`/transactions/${id}`, { method: 'DELETE' }, username);
            await refresh();
        } catch (e) {
            console.error('Failed to delete transaction:', e);
        }
    };

    const stats = [
        { icon: 'payments', label: 'Income', value: fmt(dashboard?.totalIncome ?? 0), color: 'text-emerald-accent' },
        { icon: 'credit_card', label: 'Expenses', value: fmt(dashboard?.totalExpenses ?? 0), color: 'text-crimson-accent' },
        { icon: 'savings', label: 'Net', value: fmt(dashboard?.net ?? 0), color: (dashboard?.net ?? 0) >= 0 ? 'text-emerald-accent' : 'text-crimson-accent' },
        { icon: 'category', label: 'Categories', value: `${dashboard?.categories.length ?? 0}`, color: 'text-primary' },
    ];

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
        <>
            {/* Hero Section - Balance & Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Balance Card */}
                <div className="col-span-1 lg:col-span-2 glass-panel rounded-2xl p-6 md:p-8 relative overflow-hidden group">
                    <div className="absolute -right-10 -top-10 size-64 bg-primary/20 rounded-full blur-3xl group-hover:bg-primary/30 transition-all duration-700"></div>
                    <div className="relative z-10 flex flex-col h-full justify-between gap-6">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-slate-400 font-medium mb-1">Net Balance</p>
                                <h2 className={`text-4xl md:text-5xl font-bold font-mono tracking-tight ${(dashboard?.net ?? 0) >= 0 ? 'text-white' : 'text-crimson-accent'}`}>
                                    {fmt(dashboard?.net ?? 0)}
                                </h2>
                            </div>
                            <button
                                onClick={() => setShowForm(!showForm)}
                                className="bg-primary hover:bg-blue-600 text-white p-3 rounded-xl shadow-lg shadow-blue-500/20 transition-all active:scale-95"
                            >
                                <span className="material-symbols-outlined">{showForm ? 'close' : 'add'}</span>
                            </button>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
                            {stats.map((stat) => (
                                <div
                                    key={stat.label}
                                    className="flex flex-col gap-1 p-3 rounded-xl hover:bg-white/5 transition-colors border border-transparent hover:border-white/5"
                                >
                                    <div className="text-slate-400 mb-1">
                                        <span className="material-symbols-outlined">{stat.icon}</span>
                                    </div>
                                    <span className="text-xs text-slate-500 uppercase tracking-wider">
                                        {stat.label}
                                    </span>
                                    <span className={`font-mono font-semibold ${stat.color}`}>{stat.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Category Breakdown */}
                <div className="col-span-1 flex flex-col gap-6">
                    <div className="glass-panel rounded-2xl p-6 flex-1 flex flex-col">
                        <h3 className="text-white font-medium mb-4">Spending by Category</h3>
                        {dashboard && dashboard.categories.length > 0 ? (
                            <div className="flex flex-col gap-3 flex-1">
                                {dashboard.categories.map((cat) => {
                                    const max = Math.max(...dashboard.categories.map(c => c.totalSpent), 1);
                                    const pct = (cat.totalSpent / max) * 100;
                                    const style = getCategoryStyle(cat.category);
                                    return (
                                        <div key={cat.category}>
                                            <div className="flex items-center justify-between text-xs mb-1">
                                                <span className={`flex items-center gap-1.5 ${style.color}`}>
                                                    <span className="material-symbols-outlined text-sm">{style.icon}</span>
                                                    {cat.category}
                                                </span>
                                                <span className="text-white font-mono">{fmt(cat.totalSpent)}</span>
                                            </div>
                                            <div className="w-full bg-slate-700/30 h-1.5 rounded-full overflow-hidden">
                                                <div className="bg-primary h-full rounded-full transition-all" style={{ width: `${pct}%` }}></div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <p className="text-slate-500 text-sm flex-1 flex items-center justify-center">No spending data yet</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Net Balance Trend */}
            {transactions.length > 0 && (() => {
                // Build daily running balance from transactions sorted by date
                const sorted = [...transactions].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
                const dailyMap = new Map<string, number>();
                for (const tx of sorted) {
                    const day = tx.date.slice(0, 10);
                    const prev = dailyMap.get(day) ?? 0;
                    dailyMap.set(day, prev + (tx.transactionType === 'income' ? tx.amount : -tx.amount));
                }
                // Cumulative balance per day
                const days = Array.from(dailyMap.keys()).sort();
                const points: { day: string; balance: number }[] = [];
                let running = 0;
                for (const day of days) {
                    running += dailyMap.get(day)!;
                    points.push({ day, balance: running });
                }
                if (points.length < 2) return null;

                const balances = points.map(p => p.balance);
                const minVal = Math.min(...balances);
                const maxVal = Math.max(...balances);
                const range = maxVal - minVal || 1;
                const W = 600;
                const H = 200;
                const padY = 20;

                const toX = (i: number) => (i / (points.length - 1)) * W;
                const toY = (v: number) => H - padY - ((v - minVal) / range) * (H - padY * 2);

                const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(p.balance).toFixed(1)}`).join(' ');
                const areaPath = `${linePath} L${W},${H} L0,${H} Z`;
                const zeroY = toY(0);
                const showZero = minVal < 0 && maxVal > 0;

                return (
                    <div className="glass-panel rounded-2xl p-6 md:p-8">
                        <h3 className="text-white font-medium mb-4">Net Balance Trend</h3>
                        <div className="w-full overflow-hidden">
                            <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" preserveAspectRatio="none">
                                <defs>
                                    <linearGradient id="balanceGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor={running >= 0 ? '#10b981' : '#ff003c'} stopOpacity="0.3" />
                                        <stop offset="100%" stopColor={running >= 0 ? '#10b981' : '#ff003c'} stopOpacity="0.02" />
                                    </linearGradient>
                                </defs>
                                {/* Grid lines */}
                                {[0, 0.25, 0.5, 0.75, 1].map(pct => {
                                    const y = padY + pct * (H - padY * 2);
                                    return <line key={pct} x1="0" y1={y} x2={W} y2={y} stroke="rgba(148,163,184,0.08)" strokeWidth="1" />;
                                })}
                                {/* Zero line */}
                                {showZero && (
                                    <line x1="0" y1={zeroY} x2={W} y2={zeroY} stroke="rgba(148,163,184,0.25)" strokeWidth="1" strokeDasharray="6 4" />
                                )}
                                {/* Area fill */}
                                <path d={areaPath} fill="url(#balanceGrad)" />
                                {/* Line */}
                                <path d={linePath} fill="none" stroke={running >= 0 ? '#10b981' : '#ff003c'} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
                                {/* Data points */}
                                {points.map((p, i) => (
                                    <circle key={i} cx={toX(i)} cy={toY(p.balance)} r="4" fill={p.balance >= 0 ? '#10b981' : '#ff003c'} stroke="#0f172a" strokeWidth="2" />
                                ))}
                            </svg>
                            {/* X-axis labels */}
                            <div className="flex justify-between mt-2">
                                {points.map((p, i) => (
                                    <span key={i} className="text-[10px] text-slate-500 font-mono" style={{ width: 0, textAlign: 'center', overflow: 'visible', whiteSpace: 'nowrap' }}>
                                        {new Date(p.day + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                );
            })()}

            {/* Add Transaction Form */}
            {showForm && (
                <div className="glass-panel rounded-2xl p-6 md:p-8">
                    <h3 className="text-white text-lg font-semibold mb-4">Add Transaction</h3>
                    <form onSubmit={handleAdd} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider">Description</label>
                            <input
                                type="text"
                                value={formDesc}
                                onChange={(e) => setFormDesc(e.target.value)}
                                placeholder="Coffee, Salary..."
                                required
                                className="px-3 py-2.5 rounded-lg bg-slate-900/50 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm"
                            />
                        </div>
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider">Amount</label>
                            <input
                                type="number"
                                step="0.01"
                                min="0.01"
                                value={formAmount}
                                onChange={(e) => setFormAmount(e.target.value)}
                                placeholder="0.00"
                                required
                                className="px-3 py-2.5 rounded-lg bg-slate-900/50 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm font-mono"
                            />
                        </div>
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider">Category</label>
                            <select
                                value={formCategory}
                                onChange={(e) => setFormCategory(e.target.value)}
                                className="px-3 py-2.5 rounded-lg bg-slate-900/50 border border-slate-800 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm appearance-none"
                            >
                                {CATEGORIES.map((c) => (
                                    <option key={c.name} value={c.name}>{c.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider">Type</label>
                            <div className="flex rounded-lg overflow-hidden border border-slate-800">
                                <button
                                    type="button"
                                    onClick={() => setFormType('expense')}
                                    className={`flex-1 py-2.5 text-sm font-medium transition-colors ${formType === 'expense' ? 'bg-crimson-accent/20 text-crimson-accent' : 'bg-slate-900/50 text-slate-400 hover:text-white'}`}
                                >
                                    Expense
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setFormType('income')}
                                    className={`flex-1 py-2.5 text-sm font-medium transition-colors ${formType === 'income' ? 'bg-emerald-accent/20 text-emerald-accent' : 'bg-slate-900/50 text-slate-400 hover:text-white'}`}
                                >
                                    Income
                                </button>
                            </div>
                        </div>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="py-2.5 rounded-lg bg-primary hover:bg-blue-600 disabled:opacity-40 text-white text-sm font-semibold transition-colors"
                        >
                            {submitting ? 'Adding...' : 'Add'}
                        </button>
                    </form>
                </div>
            )}

            {/* Transactions Table */}
            <div className="glass-panel rounded-2xl p-6 md:p-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <div>
                        <h3 className="text-white text-lg font-semibold">Recent Transactions</h3>
                        <p className="text-slate-500 text-sm">
                            {transactions.length === 0 ? 'No transactions yet. Add one above!' : `${transactions.length} transaction${transactions.length !== 1 ? 's' : ''}`}
                        </p>
                    </div>
                </div>
                {transactions.length > 0 && (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-slate-800/80">
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Description</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Category</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Amount</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-center w-16"></th>
                                </tr>
                            </thead>
                            <tbody className="text-sm">
                                {transactions.map((tx) => {
                                    const isIncome = tx.transactionType === 'income';
                                    const catStyle = getCategoryStyle(tx.category);
                                    return (
                                        <tr
                                            key={tx.id}
                                            className="group hover:bg-slate-800/30 transition-colors border-b border-slate-800/40 last:border-0"
                                        >
                                            <td className="py-4 px-4 text-white flex items-center gap-3">
                                                <div className={`size-8 rounded-full flex items-center justify-center ${catStyle.bg} ${catStyle.color}`}>
                                                    <span className="material-symbols-outlined text-sm">{catStyle.icon}</span>
                                                </div>
                                                <span className="font-medium">{tx.description}</span>
                                            </td>
                                            <td className={`py-4 px-4 ${catStyle.color}`}>{tx.category}</td>
                                            <td className="py-4 px-4 text-slate-400">{fmtDate(tx.date)}</td>
                                            <td className={`py-4 px-4 text-right font-mono font-medium ${isIncome ? 'text-emerald-accent' : 'text-crimson-accent'}`}>
                                                {isIncome ? '+' : '-'}{fmt(tx.amount)}
                                            </td>
                                            <td className="py-4 px-4 text-center">
                                                <button
                                                    onClick={() => handleDelete(tx.id)}
                                                    className="p-1 rounded text-slate-600 hover:text-crimson-accent hover:bg-crimson-accent/10 transition-colors opacity-0 group-hover:opacity-100"
                                                    title="Delete"
                                                >
                                                    <span className="material-symbols-outlined text-lg">delete</span>
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <div className="h-8"></div>
        </>
    );
}
