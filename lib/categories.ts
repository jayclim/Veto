export interface CategoryDef {
  name: string;
  icon: string;
  color: string;
  border: string;
  bg: string;
}

export const CATEGORIES: CategoryDef[] = [
  { name: 'Food & Dining',    icon: 'restaurant',      color: 'text-electric-blue', border: 'border-l-electric-blue', bg: 'bg-blue-500/10' },
  { name: 'Housing',          icon: 'home',             color: 'text-purple-400',    border: 'border-l-purple-500',    bg: 'bg-purple-500/10' },
  { name: 'Transportation',   icon: 'directions_car',   color: 'text-orange-400',    border: 'border-l-orange-500',    bg: 'bg-orange-500/10' },
  { name: 'Entertainment',    icon: 'movie',            color: 'text-pink-400',      border: 'border-l-pink-500',      bg: 'bg-pink-500/10' },
  { name: 'Shopping',         icon: 'shopping_bag',     color: 'text-yellow-400',    border: 'border-l-yellow-500',    bg: 'bg-yellow-500/10' },
  { name: 'Subscriptions',    icon: 'subscriptions',    color: 'text-green-400',     border: 'border-l-green-500',     bg: 'bg-green-500/10' },
  { name: 'Health',           icon: 'health_and_safety',color: 'text-red-400',       border: 'border-l-red-500',       bg: 'bg-red-500/10' },
  { name: 'Education',        icon: 'school',           color: 'text-indigo-400',    border: 'border-l-indigo-500',    bg: 'bg-indigo-500/10' },
  { name: 'Utilities',        icon: 'bolt',             color: 'text-amber-400',     border: 'border-l-amber-500',     bg: 'bg-amber-500/10' },
  { name: 'Savings',          icon: 'savings',          color: 'text-teal-400',      border: 'border-l-teal-500',      bg: 'bg-teal-500/10' },
  { name: 'Income',           icon: 'payments',         color: 'text-emerald-accent', border: 'border-l-emerald-accent', bg: 'bg-emerald-accent/10' },
  { name: 'Other',            icon: 'category',         color: 'text-slate-300',     border: 'border-l-slate-500',     bg: 'bg-slate-500/10' },
];

const CATEGORY_MAP = new Map(CATEGORIES.map(c => [c.name, c]));

const DEFAULT_STYLE: CategoryDef = { name: 'Other', icon: 'category', color: 'text-slate-300', border: 'border-l-slate-500', bg: 'bg-slate-500/10' };

export function getCategoryStyle(name: string): CategoryDef {
  return CATEGORY_MAP.get(name) ?? DEFAULT_STYLE;
}
