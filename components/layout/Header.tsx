'use client';

import { useAuth } from '@/context/AuthContext';

interface HeaderProps {
    isChatVisible: boolean;
    onToggleChat: () => void;
}

export default function Header({ isChatVisible, onToggleChat }: HeaderProps) {
    const { username, logout } = useAuth();
    return (
        <header className="flex items-center justify-between border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-md px-8 py-4 z-20">
            <div className="flex items-center gap-4">
                <button className="md:hidden text-slate-400 hover:text-white">
                    <span className="material-symbols-outlined">menu</span>
                </button>
                <h2 className="text-white text-xl font-semibold tracking-tight hidden sm:block">
                    Overview
                </h2>
            </div>
            <div className="flex items-center gap-6">
                {/* Search */}
                <div className="relative hidden md:block group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <span className="material-symbols-outlined text-slate-500 group-focus-within:text-primary transition-colors">
                            search
                        </span>
                    </div>
                    <input
                        className="block w-64 pl-10 pr-3 py-2 border border-slate-800 rounded-lg leading-5 bg-slate-900/50 text-slate-300 placeholder-slate-500 focus:outline-none focus:bg-slate-900 focus:border-primary focus:ring-1 focus:ring-primary sm:text-sm transition-all"
                        placeholder="Search assets, txs..."
                        type="text"
                    />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3">
                    {!isChatVisible && (
                        <button
                            className="cursor-pointer p-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                            onClick={onToggleChat}
                            title="Open AI Assistant"
                        >
                            <span className="material-symbols-outlined">smart_toy</span>
                        </button>
                    )}
                </div>

                <div className="h-8 w-px bg-slate-800 mx-2"></div>

                {/* User & Logout */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center size-8 rounded-full bg-primary/20 text-primary text-sm font-bold uppercase">
                        {username?.[0] ?? '?'}
                    </div>
                    <span className="text-sm text-slate-300 font-medium hidden sm:inline">{username}</span>
                    <button
                        onClick={logout}
                        className="p-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                        title="Logout"
                    >
                        <span className="material-symbols-outlined text-lg">logout</span>
                    </button>
                </div>
            </div>
        </header>
    );
}
