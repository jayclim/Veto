"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export default function LoginScreen() {
  const { login } = useAuth();
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    login(trimmed);
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-950 bg-glow-radial">
      <div className="glass-panel rounded-2xl p-10 w-full max-w-md flex flex-col items-center gap-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3">
          <div className="bg-gradient-to-br from-primary to-blue-600 rounded-2xl size-14 flex items-center justify-center shadow-lg shadow-primary/20">
            <span className="material-symbols-outlined text-white text-3xl">
              grid_view
            </span>
          </div>
          <h1 className="text-white text-2xl font-bold tracking-tight">
            Veto
          </h1>
          <p className="text-slate-500 text-sm">
            Enter a username to get started
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Username"
            autoFocus
            className="w-full px-4 py-3 rounded-xl bg-slate-900/50 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition-all"
          />
          <button
            type="submit"
            disabled={!value.trim()}
            className="w-full py-3 rounded-xl bg-primary hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
          >
            Continue
          </button>
        </form>
      </div>
    </div>
  );
}
