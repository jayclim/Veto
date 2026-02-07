import type { Config } from 'tailwindcss';

const config: Config = {
    darkMode: 'class',
    content: [
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                primary: '#2463eb',
                'electric-blue': '#00f0ff',
                'slate-950': '#020617',
                'slate-900': '#0f172a',
                'slate-800': '#1e293b',
                'emerald-accent': '#10b981',
                'crimson-red': '#ff003c',
                'surface-glass': 'rgba(30, 41, 59, 0.4)',
                'surface-glass-hover': 'rgba(30, 41, 59, 0.6)',
            },
            fontFamily: {
                display: ['Inter', 'sans-serif'],
                mono: ['Space Mono', 'Geist Mono', 'monospace'],
            },
            backgroundImage: {
                'glass-gradient':
                    'linear-gradient(145deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
                'glow-radial':
                    'radial-gradient(circle at 50% 0%, rgba(36, 99, 235, 0.15) 0%, rgba(2, 6, 23, 0) 70%)',
            },
            boxShadow: {
                neon: '0 0 20px -5px rgba(37, 99, 235, 0.5), 0 0 10px -2px rgba(37, 99, 235, 0.3)',
                'neon-card': '0 0 40px -10px rgba(37, 99, 235, 0.6)',
            },
        },
    },
    plugins: [require('@tailwindcss/forms')],
};

export default config;
