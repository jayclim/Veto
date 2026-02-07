'use client';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiFetch } from '@/lib/api';
import { getCategoryStyle } from '@/lib/categories';

interface Transaction {
    id: string;
    amount: number;
    description: string;
    category: string;
    transactionType: 'income' | 'expense';
    date: string;
}

interface ComplianceResult {
    ruleName: string;
    ruleType: string;
    compliant: boolean | null;
    message: string | null;
    targetSavingsPct?: number;
    actualSavingsPct?: number;
    category?: string;
    limit?: number;
    spent?: number;
    goal?: number;
    saved?: number;
    threshold?: number;
    alertTriggered?: boolean;
}

interface BudgetCompliance {
    status: string;
    totalIncome: number;
    totalExpenses: number;
    net: number;
    rules: ComplianceResult[];
}

function fmt(n: number): string {
    return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
}

function fmtDate(iso: string): string {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function getStyle(name: string) {
    return getCategoryStyle(name || 'Uncategorized');
}

export default function BudgetPage() {
    const { username } = useAuth();
    const [compliance, setCompliance] = useState<BudgetCompliance | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);

    const refresh = useCallback(async () => {
        if (!username) return;
        try {
            const [comp, txs] = await Promise.all([
                apiFetch<BudgetCompliance>('/budgets/compliance', {}, username),
                apiFetch<Transaction[]>('/transactions', {}, username),
            ]);
            setCompliance(comp);
            setTransactions(txs);
        } catch (e) {
            console.error('Failed to fetch budget data:', e);
        } finally {
            setLoading(false);
        }
    }, [username]);

    useEffect(() => { refresh(); }, [refresh]);

    const now = new Date();
    const monthLabel = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

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
                    <h2 className="text-white text-2xl font-bold tracking-tight">Budget Rules</h2>
                    <p className="text-slate-400 text-sm">{monthLabel} Compliance Check</p>
                </div>
                {/* Removed Add Category Button per request */}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    {/* Rules List */}
                    {compliance && compliance.rules.length > 0 ? (
                        <div className={`grid grid-cols-1 gap-4 ${compliance.rules.length > 1 ? 'md:grid-cols-2' : ''}`}>
                            {compliance.rules.map((rule, idx) => {
                                const isCategoryRule = rule.ruleType === 'category_limit' || rule.ruleType === 'percentage_needs' || rule.ruleType === 'percentage_wants' || rule.ruleType === 'spending_alert';
                                const style = isCategoryRule ? getStyle(rule.category || '') : { border: 'border-slate-700', bg: 'bg-slate-800', color: 'text-slate-300', icon: 'rule' };

                                let progress = 0;
                                let progressColor = 'bg-primary';
                                let mainValue = '';
                                let subValue = '';

                                if (isCategoryRule && rule.limit) {
                                    // Categories AND Needs/Wants buckets
                                    const spent = rule.spent || 0;
                                    progress = Math.min(Math.round((spent / rule.limit) * 100), 100);

                                    // For needs/wants/limits, higher usage is "warning"
                                    progressColor = progress >= 90 ? 'bg-crimson-accent' : progress >= 70 ? 'bg-yellow-500' : 'bg-primary';

                                    mainValue = fmt(spent);
                                    subValue = `/ ${fmt(rule.limit)}`;

                                    if (rule.ruleType === 'percentage_needs' || rule.ruleType === 'percentage_wants') {
                                        subValue += ` (${rule.actualSavingsPct}% / ${rule.targetSavingsPct}%)`;
                                    }
                                } else if (rule.ruleType === 'percentage_allocation') {
                                    // Savings goal (Higher is better)
                                    progress = rule.actualSavingsPct || 0;
                                    progressColor = rule.compliant ? 'bg-emerald-accent' : 'bg-crimson-accent';
                                    mainValue = `${rule.actualSavingsPct}%`;
                                    subValue = `Target: ${rule.targetSavingsPct}%`;
                                }

                                return (
                                    <div key={idx} className={`glass-panel p-5 rounded-2xl border-l-4 ${style.border} hover:translate-y-[-2px] transition-transform duration-300`}>
                                        <div className="flex justify-between items-start mb-4">
                                            <div className={`p-2 rounded-lg ${style.bg} ${style.color}`}>
                                                <span className="material-symbols-outlined">{style.icon}</span>
                                            </div>
                                            <span className={`text-xs font-mono px-2 py-1 rounded-full ${rule.compliant ? 'bg-emerald-accent/10 text-emerald-accent' : 'bg-crimson-accent/10 text-crimson-accent'}`}>
                                                {rule.compliant ? 'COMPLIANT' : 'AT RISK'}
                                            </span>
                                        </div>
                                        <h4 className="text-slate-300 text-sm font-medium mb-1">{rule.ruleName}</h4>
                                        <div className="flex items-baseline gap-1 mb-3">
                                            <span className="text-white text-xl font-bold font-mono">{mainValue}</span>
                                            <span className="text-slate-500 text-xs font-mono">{subValue}</span>
                                        </div>
                                        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full transition-all ${progressColor}`}
                                                style={{ width: `${progress}%` }}
                                            ></div>
                                        </div>
                                        {rule.message && (
                                            <p className="text-xs text-slate-500 mt-2">{rule.message}</p>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="glass-panel p-8 rounded-2xl text-center">
                            <span className="material-symbols-outlined text-4xl text-slate-600 mb-2">rule_folder</span>
                            <p className="text-slate-500">No active budget rules found.</p>
                        </div>
                    )}

                    {/* Spending Breakdown */}
                    <div className="glass-panel rounded-2xl p-6">
                        <h3 className="text-white text-lg font-semibold mb-4">Spending by Category</h3>
                        <div className="flex flex-col gap-3">
                            {(() => {
                                const spendingByCategory = transactions
                                    .filter(t => t.transactionType === 'expense')
                                    .reduce((acc, t) => {
                                        acc[t.category] = (acc[t.category] || 0) + t.amount;
                                        return acc;
                                    }, {} as Record<string, number>);

                                const list = Object.entries(spendingByCategory)
                                    .map(([cat, amount]) => ({ cat, amount }))
                                    .sort((a, b) => b.amount - a.amount);

                                const max = Math.max(...list.map(i => i.amount), 1);

                                if (list.length === 0) return <p className="text-slate-500 text-sm">No expenses recorded yet</p>;

                                return list.map((item) => {
                                    const style = getStyle(item.cat);
                                    const pct = (item.amount / max) * 100;
                                    return (
                                        <div key={item.cat}>
                                            <div className="flex items-center justify-between text-xs mb-1">
                                                <span className={`flex items-center gap-1.5 ${style.color}`}>
                                                    <span className="material-symbols-outlined text-sm">{style.icon}</span>
                                                    {item.cat}
                                                </span>
                                                <span className="text-white font-mono">{fmt(item.amount)}</span>
                                            </div>
                                            <div className="w-full bg-slate-700/30 h-1.5 rounded-full overflow-hidden">
                                                <div className="bg-primary h-full rounded-full transition-all" style={{ width: `${pct}%` }}></div>
                                            </div>
                                        </div>
                                    );
                                });
                            })()}
                        </div>
                    </div>

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
                                            <span className="text-crimson-accent font-mono font-medium">-{fmt(tx.amount)}</span>
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
                        <p className="text-slate-400 text-sm font-medium mb-2">Net Position</p>
                        <h2
                            className={`text-4xl font-bold font-mono tracking-tighter mb-4 ${(compliance?.net ?? 0) >= 0 ? 'text-white' : 'text-crimson-accent'}`}
                            style={{ textShadow: '0 0 10px rgba(36, 99, 235, 0.3)' }}
                        >
                            {fmt(compliance?.net ?? 0)}
                        </h2>
                        <div className="flex flex-col gap-3 text-center">
                            <div className="p-3 rounded-lg bg-emerald-accent/5 border border-emerald-accent/10">
                                <p className="text-emerald-accent text-lg font-bold font-mono">{fmt(compliance?.totalIncome ?? 0)}</p>
                                <p className="text-slate-500 text-xs">Income</p>
                            </div>
                            <div className="p-3 rounded-lg bg-crimson-accent/5 border border-crimson-accent/10">
                                <p className="text-crimson-accent text-lg font-bold font-mono">{fmt(compliance?.totalExpenses ?? 0)}</p>
                                <p className="text-slate-500 text-xs">Expenses</p>
                            </div>
                        </div>
                    </div>

                    {/* Tip Card */}
                    <div className="glass-panel rounded-2xl p-6 bg-primary/5 border-primary/20">
                        <div className="flex items-start gap-3">
                            <span className="material-symbols-outlined text-primary mt-1">lightbulb</span>
                            <div>
                                <h4 className="text-white font-medium text-sm mb-1">Budget Rules</h4>
                                <p className="text-slate-400 text-xs leading-relaxed">
                                    Your budget is now controlled by autonomous rules. Agents operate within these constraints to ensure financial health.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
