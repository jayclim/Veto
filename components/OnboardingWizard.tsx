"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import {
  completeOnboarding as completeOnboardingApi,
  OnboardingCompleteRequest,
} from "@/lib/api";

type BudgetStrategy = "50/30/20" | "80/20" | "custom";

const STRATEGIES: {
  id: BudgetStrategy;
  label: string;
  icon: string;
  description: string;
}[] = [
  {
    id: "50/30/20",
    label: "50/30/20 Rule",
    icon: "pie_chart",
    description:
      "50% needs, 30% wants, 20% savings. The most popular budgeting framework.",
  },
  {
    id: "80/20",
    label: "80/20 Rule",
    icon: "savings",
    description: "80% spending, 20% savings. Simple and flexible.",
  },
  {
    id: "custom",
    label: "Custom Split",
    icon: "tune",
    description: "Set your own percentages for needs, wants, and savings.",
  },
];

export default function OnboardingWizard() {
  const { username, completeOnboarding } = useAuth();

  const [step, setStep] = useState(1);
  const [monthlyIncome, setMonthlyIncome] = useState(5000);
  const [strategy, setStrategy] = useState<BudgetStrategy>("50/30/20");
  const [customNeeds, setCustomNeeds] = useState(50);
  const [customWants, setCustomWants] = useState(30);
  const [customSavings, setCustomSavings] = useState(20);

  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const customSum = customNeeds + customWants + customSavings;
  const customValid = customSum === 100;

  const [retryCount, setRetryCount] = useState(0);

  // Step 4: fire the API call on mount
  useEffect(() => {
    if (step !== 4) return;

    const run = async () => {
      setLoading(true);
      setError(null);

      // Map display IDs to API strategy keys
      const strategyKey =
        strategy === "50/30/20" ? "50_30_20" : strategy === "80/20" ? "80_20" : "custom";

      const payload: OnboardingCompleteRequest = {
        monthly_income: monthlyIncome,
        budget_strategy: strategyKey,
      };

      if (strategy === "50/30/20") {
        payload.needs_pct = 50;
        payload.wants_pct = 30;
        payload.savings_pct = 20;
      } else if (strategy === "80/20") {
        payload.needs_pct = 80;
        payload.wants_pct = 0;
        payload.savings_pct = 20;
      } else {
        payload.needs_pct = customNeeds;
        payload.wants_pct = customWants;
        payload.savings_pct = customSavings;
      }

      try {
        await completeOnboardingApi(payload, username!);
        setDone(true);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Something went wrong.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, retryCount]);

  /* ------------------------------------------------------------------ */
  /*  Step indicator                                                     */
  /* ------------------------------------------------------------------ */
  const StepIndicator = () => (
    <div className="flex items-center justify-center gap-2 mb-8">
      {[1, 2, 3, 4].map((s) => (
        <div
          key={s}
          className={`size-2.5 rounded-full transition-colors duration-300 ${
            s <= step
              ? "bg-primary"
              : "bg-slate-700"
          }`}
        />
      ))}
    </div>
  );

  /* ------------------------------------------------------------------ */
  /*  Step 1 — Welcome                                                   */
  /* ------------------------------------------------------------------ */
  const renderStep1 = () => (
    <div className="flex flex-col items-center gap-6 text-center">
      <div className="flex flex-col items-center gap-3">
        <div className="bg-gradient-to-br from-primary to-blue-600 rounded-2xl size-14 flex items-center justify-center shadow-lg shadow-primary/20">
          <span className="material-symbols-outlined text-white text-3xl">
            grid_view
          </span>
        </div>
        <h1 className="text-white text-2xl font-bold tracking-tight">
          Welcome to Veto
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
          Your AI-powered budget guardian. Let&rsquo;s set up your finances in
          under a minute.
        </p>
      </div>

      <button
        onClick={() => setStep(2)}
        className="w-full py-3 rounded-xl bg-primary hover:bg-blue-600 text-white text-sm font-semibold transition-colors"
      >
        Get Started
      </button>
    </div>
  );

  /* ------------------------------------------------------------------ */
  /*  Step 2 — Monthly Income                                            */
  /* ------------------------------------------------------------------ */
  const renderStep2 = () => (
    <div className="flex flex-col items-center gap-6 w-full">
      <div className="text-center">
        <h2 className="text-white text-xl font-bold tracking-tight">
          What&rsquo;s your monthly income?
        </h2>
        <p className="text-slate-500 text-sm mt-2">
          This helps us create realistic sample data and budget rules.
        </p>
      </div>

      <div className="relative w-full">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-lg font-semibold">
          $
        </span>
        <input
          type="number"
          value={monthlyIncome}
          onChange={(e) => setMonthlyIncome(Number(e.target.value))}
          min={0}
          autoFocus
          className="w-full pl-9 pr-4 py-3 rounded-xl bg-slate-900/50 border border-slate-800 text-white text-lg font-semibold placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        />
      </div>

      <button
        onClick={() => setStep(3)}
        disabled={monthlyIncome <= 0}
        className="w-full py-3 rounded-xl bg-primary hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
      >
        Continue
      </button>
    </div>
  );

  /* ------------------------------------------------------------------ */
  /*  Step 3 — Budget Strategy                                           */
  /* ------------------------------------------------------------------ */
  const renderStep3 = () => (
    <div className="flex flex-col items-center gap-6 w-full">
      <h2 className="text-white text-xl font-bold tracking-tight text-center">
        Choose your budget strategy
      </h2>

      <div className="flex flex-col gap-3 w-full">
        {STRATEGIES.map((s) => (
          <button
            key={s.id}
            onClick={() => setStrategy(s.id)}
            className={`w-full text-left px-4 py-4 rounded-xl border transition-all ${
              strategy === s.id
                ? "border-primary bg-primary/10"
                : "border-slate-800 bg-slate-900/50 hover:border-slate-700"
            }`}
          >
            <div className="flex items-start gap-3">
              <span
                className={`material-symbols-outlined mt-0.5 text-xl ${
                  strategy === s.id ? "text-primary" : "text-slate-400"
                }`}
              >
                {s.icon}
              </span>
              <div>
                <p className="text-white text-sm font-semibold">{s.label}</p>
                <p className="text-slate-400 text-xs mt-0.5 leading-relaxed">
                  {s.description}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Custom split inputs */}
      {strategy === "custom" && (
        <div className="w-full flex flex-col gap-3">
          <div className="grid grid-cols-3 gap-3">
            {([
              ["Needs %", customNeeds, setCustomNeeds],
              ["Wants %", customWants, setCustomWants],
              ["Savings %", customSavings, setCustomSavings],
            ] as [string, number, (v: number) => void][]).map(
              ([label, val, setter]) => (
                <div key={label} className="flex flex-col gap-1">
                  <label className="text-slate-500 text-xs">{label}</label>
                  <input
                    type="number"
                    value={val}
                    onChange={(e) => setter(Number(e.target.value))}
                    min={0}
                    max={100}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-800 text-white text-sm text-center placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  />
                </div>
              )
            )}
          </div>
          {!customValid && (
            <p className="text-red-400 text-xs text-center">
              Percentages must add up to 100 (currently {customSum}).
            </p>
          )}
        </div>
      )}

      <button
        onClick={() => setStep(4)}
        disabled={strategy === "custom" && !customValid}
        className="w-full py-3 rounded-xl bg-primary hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
      >
        Continue
      </button>
    </div>
  );

  /* ------------------------------------------------------------------ */
  /*  Step 4 — Setting Up / Done                                         */
  /* ------------------------------------------------------------------ */
  const renderStep4 = () => (
    <div className="flex flex-col items-center gap-6 text-center py-4">
      {loading && (
        <>
          <span className="material-symbols-outlined text-primary text-5xl animate-pulse">
            hourglass_top
          </span>
          <p className="text-slate-400 text-sm">Setting up your account...</p>
        </>
      )}

      {done && (
        <>
          <div className="bg-emerald-500/20 rounded-full size-16 flex items-center justify-center">
            <span className="material-symbols-outlined text-emerald-400 text-4xl">
              check_circle
            </span>
          </div>
          <h2 className="text-white text-xl font-bold tracking-tight">
            You&rsquo;re all set!
          </h2>
          <button
            onClick={() => completeOnboarding()}
            className="w-full py-3 rounded-xl bg-primary hover:bg-blue-600 text-white text-sm font-semibold transition-colors"
          >
            Go to Dashboard
          </button>
        </>
      )}

      {error && (
        <>
          <div className="bg-red-500/20 rounded-full size-16 flex items-center justify-center">
            <span className="material-symbols-outlined text-red-400 text-4xl">
              error
            </span>
          </div>
          <p className="text-red-400 text-sm">{error}</p>
          <button
            onClick={() => {
              setDone(false);
              setError(null);
              setRetryCount((c) => c + 1);
            }}
            className="w-full py-3 rounded-xl bg-primary hover:bg-blue-600 text-white text-sm font-semibold transition-colors"
          >
            Retry
          </button>
        </>
      )}
    </div>
  );

  /* ------------------------------------------------------------------ */
  /*  Layout                                                             */
  /* ------------------------------------------------------------------ */
  const stepContent: Record<number, () => JSX.Element> = {
    1: renderStep1,
    2: renderStep2,
    3: renderStep3,
    4: renderStep4,
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-950 bg-glow-radial">
      <div className="glass-panel rounded-2xl p-10 w-full max-w-lg flex flex-col">
        <StepIndicator />
        <div className="transition-opacity duration-300">
          {stepContent[step]()}
        </div>
      </div>
    </div>
  );
}
