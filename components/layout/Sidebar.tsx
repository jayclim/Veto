'use client';

import { useState } from 'react';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
    { href: '/', label: 'Dashboard', icon: 'dashboard' },
    { href: '/budget', label: 'Budget', icon: 'account_balance_wallet' },
    { href: '/cards', label: 'Cards', icon: 'credit_card' },
];

export default function Sidebar() {
    const pathname = usePathname();
    const [isCollapsed, setIsCollapsed] = useState(false);

    return (
        <aside
            className={`${isCollapsed ? 'w-20' : 'w-72'} flex-shrink-0 border-r border-slate-800/50 bg-slate-950/50 backdrop-blur-xl flex flex-col justify-between p-4 hidden md:flex z-30 transition-all duration-300 ease-in-out`}
        >
            <div className="flex flex-col gap-8">
                {/* Logo */}
                <div className={`flex items-center gap-3 px-2 ${isCollapsed ? 'justify-center' : ''}`}>
                    <div className="bg-gradient-to-br from-primary to-blue-600 aspect-square rounded-xl size-10 flex items-center justify-center shadow-lg shadow-primary/20 flex-shrink-0">
                        <span className="material-symbols-outlined text-white text-xl">grid_view</span>
                    </div>
                    {!isCollapsed && (
                        <div className="flex flex-col overflow-hidden whitespace-nowrap transition-opacity duration-300">
                            <h1 className="text-white text-lg font-bold tracking-tight">Veto</h1>
                            <p className="text-slate-500 text-xs font-medium uppercase tracking-wider">
                                Budget Manager
                            </p>
                        </div>
                    )}
                </div>

                {/* Navigation */}
                <nav className="flex flex-col gap-2">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all group ${isActive
                                    ? 'bg-primary/10 border border-primary/20 text-white'
                                    : 'hover:bg-slate-800/50 text-slate-400 hover:text-white border border-transparent'
                                    } ${isCollapsed ? 'justify-center px-2' : ''}`}
                                title={isCollapsed ? item.label : undefined}
                            >
                                <span
                                    className={`material-symbols-outlined group-hover:scale-110 transition-transform ${isActive ? 'text-primary' : ''
                                        }`}
                                >
                                    {item.icon}
                                </span>
                                {!isCollapsed && (
                                    <span className="text-sm font-medium whitespace-nowrap overflow-hidden transition-opacity duration-300">
                                        {item.label}
                                    </span>
                                )}
                            </Link>
                        );
                    })}
                </nav>
            </div>

            {/* Collapse Toggle */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-slate-800/50 text-slate-400 hover:text-white transition-all group ${isCollapsed ? 'justify-center' : ''}`}
            >
                <span className="material-symbols-outlined group-hover:scale-110 transition-transform">
                    {isCollapsed ? 'chevron_right' : 'chevron_left'}
                </span>
                {!isCollapsed && (
                    <span className="text-sm font-medium whitespace-nowrap overflow-hidden transition-opacity duration-300">
                        Collapse Sidebar
                    </span>
                )}
            </button>
        </aside>
    );
}
