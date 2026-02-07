'use client';

import { useState } from 'react';
import Sidebar from './Sidebar';
import ChatPanel from './ChatPanel';
import Header from './Header';
import LoginScreen from '@/components/LoginScreen';
import { useAuth } from '@/context/AuthContext';

interface AppLayoutProps {
    children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
    const { username } = useAuth();
    const [isChatVisible, setIsChatVisible] = useState(true);

    if (!username) {
        return <LoginScreen />;
    }

    return (
        <div className="flex h-screen w-full bg-slate-950 bg-glow-radial relative">
            <Sidebar />
            <main className="flex-1 flex flex-col h-full overflow-hidden relative transition-all duration-500 ease-in-out">
                <Header
                    isChatVisible={isChatVisible}
                    onToggleChat={() => setIsChatVisible(!isChatVisible)}
                />
                <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
                    <div className="max-w-7xl mx-auto flex flex-col gap-6">{children}</div>
                </div>
            </main>
            <ChatPanel isVisible={isChatVisible} onToggle={() => setIsChatVisible(!isChatVisible)} />
        </div>
    );
}
