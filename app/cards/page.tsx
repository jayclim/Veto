'use client';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiFetch } from '@/lib/api';

interface Transaction {
    id: string;
    amount: number;
    description: string;
    category: string;
    transactionType: 'income' | 'expense';
    date: string;
}

interface DashboardCompliance {
    totalIncome: number;
    totalExpenses: number;
    net: number;
    // rules: ... we don't strictly need rules here for the card view, just totals
}

function fmt(n: number): string {
    return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

function fmtDate(iso: string): string {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function CardsPage() {
    const { username } = useAuth();
    const [dashboard, setDashboard] = useState<DashboardCompliance | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);

    const refresh = useCallback(async () => {
        if (!username) return;
        try {
            const [dash, txs] = await Promise.all([
                apiFetch<DashboardCompliance>('/budgets/compliance', {}, username),
                apiFetch<Transaction[]>('/transactions', {}, username),
            ]);
            setDashboard(dash);
            setTransactions(txs);
        } catch (e) {
            console.error('Failed to fetch card data:', e);
        } finally {
            setLoading(false);
        }
    }, [username]);

    useEffect(() => { refresh(); }, [refresh]);

    const totalExpenses = dashboard?.totalExpenses ?? 0;
    const recentExpenses = transactions.filter(t => t.transactionType === 'expense').slice(0, 5);

    // Build category bar chart data from transactions
    const catData = Object.entries(
        transactions
            .filter(t => t.transactionType === 'expense')
            .reduce((acc, t) => {
                acc[t.category] = (acc[t.category] || 0) + (+t.amount);
                return acc;
            }, {} as Record<string, number>)
    ).map(([category, totalSpent]) => ({ category, totalSpent }))
        .sort((a, b) => b.totalSpent - a.totalSpent);

    const maxCatSpent = Math.max(...catData.map(c => c.totalSpent), 1);

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
        <div className="flex flex-col gap-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">Accounts & Cards</h2>
                    <div className="flex items-center gap-2 mt-0.5">
                        <div className="size-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
                        <span className="text-xs text-slate-400 font-mono">Synced just now</span>
                    </div>
                </div>
            </div>

            {/* Top Section: Card & Stats */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left: Visa Card */}
                <div className="lg:col-span-5 flex flex-col gap-6">
                    <div className="relative w-full aspect-[1.586/1] rounded-2xl p-6 flex flex-col justify-between overflow-hidden group bg-gradient-to-br from-slate-900 via-slate-800 to-primary/30">
                        <div className="absolute inset-0 border border-white/10 rounded-2xl z-10 pointer-events-none"></div>
                        <div className="absolute -right-20 -top-20 w-64 h-64 bg-primary/40 blur-[80px] rounded-full z-0"></div>

                        <div className="relative z-20 flex justify-between items-start">
                            <span className="material-symbols-outlined text-white text-[32px]">contactless</span>
                            <span className="text-white font-bold italic text-xl tracking-wider opacity-90">VISA</span>
                        </div>
                        <div className="relative z-20 flex flex-col gap-8">
                            <div className="w-12 h-8 rounded bg-yellow-200/20 border border-yellow-200/30 backdrop-blur-sm"></div>
                            <div className="flex justify-between items-end">
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-slate-300 uppercase tracking-widest">Balance</span>
                                    <span className="text-3xl text-white font-mono font-bold tracking-tight">{fmt(dashboard?.net ?? 0)}</span>
                                </div>
                            </div>
                            <div className="flex justify-between items-end">
                                <span className="text-slate-300 text-sm font-mono tracking-widest">**** **** **** 4289</span>
                                <div className="flex flex-col items-end">
                                    <span className="text-[10px] text-slate-400 uppercase">Expires</span>
                                    <span className="text-white text-sm font-mono">12/28</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Card Actions */}
                    <div className="grid grid-cols-3 gap-3">
                        <button className="flex flex-col items-center justify-center gap-2 py-4 rounded-xl glass-panel hover:bg-white/5 border border-white/5 transition-all group">
                            <div className="size-10 rounded-full bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
                                <span className="material-symbols-outlined text-blue-400">ac_unit</span>
                            </div>
                            <span className="text-xs font-medium text-slate-300">Freeze</span>
                        </button>
                        <button className="flex flex-col items-center justify-center gap-2 py-4 rounded-xl glass-panel hover:bg-white/5 border border-white/5 transition-all group">
                            <div className="size-10 rounded-full bg-purple-500/10 flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
                                <span className="material-symbols-outlined text-purple-400">visibility</span>
                            </div>
                            <span className="text-xs font-medium text-slate-300">Show PIN</span>
                        </button>
                        <button className="flex flex-col items-center justify-center gap-2 py-4 rounded-xl glass-panel hover:bg-white/5 border border-white/5 transition-all group">
                            <div className="size-10 rounded-full bg-slate-500/10 flex items-center justify-center group-hover:bg-slate-500/20 transition-colors">
                                <span className="material-symbols-outlined text-slate-400">settings</span>
                            </div>
                            <span className="text-xs font-medium text-slate-300">Settings</span>
                        </button>
                    </div>
                </div>

                {/* Right: Spending Analytics */}
                <div className="lg:col-span-7 flex flex-col gap-6">
                    <div className="glass-panel rounded-xl p-6 h-full flex flex-col">
                        <h3 className="text-lg font-semibold text-white mb-6">Spending Analytics</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                            <div className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                                <p className="text-slate-400 text-xs font-medium mb-1">Total Spent</p>
                                <p className="text-white text-xl font-bold tracking-tight font-mono">{fmt(totalExpenses)}</p>
                            </div>
                            <div className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                                <p className="text-slate-400 text-xs font-medium mb-1">Total Income</p>
                                <p className="text-emerald-accent text-xl font-bold tracking-tight font-mono">{fmt(dashboard?.totalIncome ?? 0)}</p>
                            </div>
                            <div className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                                <p className="text-slate-400 text-xs font-medium mb-1">Categories</p>
                                <p className="text-white text-xl font-bold tracking-tight font-mono">{catData.length}</p>
                            </div>
                        </div>

                        {/* Category bar chart */}
                        <div className="flex-1 w-full rounded-lg border border-white/5 relative overflow-hidden flex items-end px-2 pt-8 pb-0 gap-2 bg-gradient-to-t from-primary/5 to-transparent min-h-[140px]">
                            {catData.length > 0 ? (
                                catData.map((cat, i) => {
                                    const pct = Math.max((cat.totalSpent / maxCatSpent) * 100, 5);
                                    const isLast = i === catData.length - 1;
                                    return (
                                        <div key={cat.category} className="flex flex-col items-center justify-end h-full flex-1 gap-1 group" title={`${cat.category}: ${fmt(cat.totalSpent)}`}>
                                            <span className="text-[9px] text-slate-500 font-mono opacity-0 group-hover:opacity-100 transition-opacity mb-auto">{fmt(cat.totalSpent)}</span>
                                            <div
                                                className={`w-full rounded-t-sm transition-all ${isLast ? 'bg-primary/60 hover:bg-primary shadow-[0_0_15px_rgba(37,99,235,0.4)]' : 'bg-primary/20 hover:bg-primary/40'}`}
                                                style={{ height: `${pct}%` }}
                                            ></div>
                                            <span className="text-[9px] text-slate-500 truncate max-w-full px-0.5">{cat.category}</span>
                                        </div>
                                    );
                                })
                            ) : (
                                <div className="flex-1 flex items-center justify-center text-slate-500 text-sm pb-8">No spending data yet</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Linked Accounts */}
            <div className="flex flex-col gap-4">
                <h3 className="text-lg font-semibold text-white">Linked Accounts</h3>
                <div className="glass-panel rounded-xl overflow-hidden">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-white/10 bg-slate-900/30">
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Institution</th>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Account Type</th>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Account #</th>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Balance</th>
                                <th className="p-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {/* Visa Credit Card */}
                            <tr className="group hover:bg-white/[0.02] transition-colors">
                                <td className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="size-10 rounded-lg bg-[#1a1f71] flex items-center justify-center">
                                            <span className="text-white font-bold italic text-xs">VISA</span>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-white">Visa</p>
                                            <p className="text-xs text-slate-500">Primary Card</p>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                                        Credit Card
                                    </span>
                                </td>
                                <td className="p-4 font-mono text-xs text-slate-400">•••• 4289</td>
                                <td className="p-4 text-right">
                                    <span className="text-sm font-bold text-white font-mono">{fmt(dashboard?.net ?? 0)}</span>
                                </td>
                                <td className="p-4 text-center">
                                    <div className="size-2 rounded-full bg-emerald-500 mx-auto shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                                </td>
                            </tr>
                            {/* Capital One Checking */}
                            <tr className="group hover:bg-white/[0.02] transition-colors">
                                <td className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="size-10 rounded-lg bg-[#d03027] flex items-center justify-center">
                                            <span className="text-white font-bold text-xs">C1</span>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-white">Capital One</p>
                                            <p className="text-xs text-slate-500">Linked Bank</p>
                                        </div>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                                        360 Checking
                                    </span>
                                </td>
                                <td className="p-4 font-mono text-xs text-slate-400">•••• 8829</td>
                                <td className="p-4 text-right">
                                    <span className="text-sm font-bold text-emerald-accent font-mono">{fmt(dashboard?.totalIncome ?? 0)}</span>
                                </td>
                                <td className="p-4 text-center">
                                    <div className="size-2 rounded-full bg-emerald-500 mx-auto shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Recent Card Transactions */}
            {recentExpenses.length > 0 && (
                <div className="glass-panel rounded-2xl p-6">
                    <h3 className="text-white text-lg font-semibold mb-4">Recent Card Activity</h3>
                    <div className="space-y-3">
                        {recentExpenses.map((tx) => (
                            <div key={tx.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors border border-transparent hover:border-white/5">
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-white border border-slate-700">
                                        <span className="material-symbols-outlined text-[20px]">arrow_upward</span>
                                    </div>
                                    <div>
                                        <p className="text-white font-medium text-sm">{tx.description}</p>
                                        <p className="text-slate-500 text-xs">{fmtDate(tx.date)} &middot; {tx.category}</p>
                                    </div>
                                </div>
                                <span className="text-crimson-accent font-mono font-medium">-{fmt(tx.amount)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
