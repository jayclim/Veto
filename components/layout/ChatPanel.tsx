'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { sendChatMessageStream, ActionResult, StreamEvent } from '@/lib/api';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    richContent?: React.ReactNode;
}

interface ChatPanelProps {
    isVisible: boolean;
    onToggle: () => void;
}

export default function ChatPanel({ isVisible, onToggle }: ChatPanelProps) {
    const { username } = useAuth();
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content:
                'Welcome! I can help you understand your spending patterns and manage your budget. Try asking me about your recent transactions or say "add a $50 expense for groceries" to add a transaction.',
            timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
        },
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const formatActionConfirmation = (action: ActionResult): string => {
        if (!action.success) {
            return `Failed to ${action.type.replace(/_/g, ' ')}: ${action.error || 'Unknown error'}`;
        }

        switch (action.type) {
            case 'add_transaction':
                return `Added transaction: ${action.details?.description} - $${action.details?.amount}`;
            case 'delete_transaction':
                return `Deleted transaction successfully`;
            default:
                return `Action completed: ${action.type}`;
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || !username) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
        };

        const assistantMsgId = (Date.now() + 1).toString();

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);
        setError(null);

        try {
            const conversationHistory = messages.slice(-10).map((m) => ({
                role: m.role,
                content: m.content,
            }));

            let streamingStarted = false;

            await sendChatMessageStream(input, conversationHistory, username, (event: StreamEvent) => {
                if (event.type === 'token' && event.content) {
                    if (!streamingStarted) {
                        // First token: create the assistant message and hide typing dots
                        streamingStarted = true;
                        setIsTyping(false);
                        setMessages((prev) => [
                            ...prev,
                            {
                                id: assistantMsgId,
                                role: 'assistant' as const,
                                content: event.content!,
                                timestamp: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
                            },
                        ]);
                    } else {
                        // Subsequent tokens: append to existing message
                        setMessages((prev) =>
                            prev.map((msg) =>
                                msg.id === assistantMsgId
                                    ? { ...msg, content: msg.content + event.content }
                                    : msg
                            )
                        );
                    }
                } else if (event.type === 'actions' && event.actions) {
                    const actionMessages = event.actions.map(formatActionConfirmation).join('\n');
                    if (actionMessages) {
                        setMessages((prev) =>
                            prev.map((msg) =>
                                msg.id === assistantMsgId
                                    ? { ...msg, content: msg.content + '\n\n' + actionMessages }
                                    : msg
                            )
                        );
                    }
                    // Trigger dashboard refresh for any successful actions
                    if (event.actions.some((a) => a.success)) {
                        window.dispatchEvent(new CustomEvent('veto-data-refresh'));
                    }
                }
                // type === 'done' — nothing extra needed
            });
        } catch (err) {
            console.error('Chat error:', err);
            setError('Failed to get response. Please try again.');
            // Update the streaming message with error text
            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === assistantMsgId
                        ? { ...msg, content: "I'm sorry, I encountered an error processing your request. Please try again." }
                        : msg
                )
            );
        } finally {
            setIsTyping(false);
        }
    };

    if (!isVisible) {
        return null;
    }

    return (
        <aside className="w-96 flex-shrink-0 flex flex-col transition-all duration-500 ease-in-out border-l border-white/10 glass-panel bg-slate-950/40 backdrop-blur-md relative h-full overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/5 bg-slate-900/40 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <div className="size-8 rounded-lg bg-gradient-to-tr from-primary to-purple-500 flex items-center justify-center text-white shadow-lg shadow-primary/20">
                            <span className="material-symbols-outlined text-sm">smart_toy</span>
                        </div>
                        <span className="absolute -bottom-1 -right-1 flex size-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-accent opacity-75"></span>
                            <span className="relative inline-flex rounded-full size-3 bg-emerald-accent border-2 border-slate-900"></span>
                        </span>
                    </div>
                    <div>
                        <h3 className="text-white font-semibold text-sm">Veto AI</h3>
                        <p className="text-[10px] text-emerald-accent font-medium uppercase tracking-wider">
                            Online
                        </p>
                    </div>
                </div>
                <button
                    className="p-2 rounded-lg text-slate-400 hover:bg-white/5 hover:text-white transition-colors cursor-pointer flex items-center justify-center"
                    onClick={onToggle}
                    title="Collapse Panel"
                >
                    <span className="material-symbols-outlined text-lg">chevron_right</span>
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
                {/* Date Separator */}
                <div className="flex items-center justify-center py-4">
                    <span className="text-[10px] text-slate-500 bg-slate-900/50 px-3 py-1 rounded-full border border-white/5">
                        Today
                    </span>
                </div>

                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                        {message.role === 'assistant' ? (
                            <div className="size-8 rounded-lg bg-gradient-to-tr from-primary to-purple-500 flex-shrink-0 flex items-center justify-center text-white text-xs">
                                AI
                            </div>
                        ) : (
                            <div className="size-8 rounded-full bg-primary/20 text-primary flex-shrink-0 flex items-center justify-center text-xs font-bold uppercase">
                                {username?.[0] ?? '?'}
                            </div>
                        )}
                        <div
                            className={`flex flex-col gap-1 max-w-[85%] ${message.role === 'user' ? 'items-end' : ''
                                }`}
                        >
                            <div
                                className={`p-3 rounded-2xl ${message.role === 'assistant'
                                    ? 'bg-slate-800/80 rounded-tl-none border border-white/5 shadow-sm'
                                    : 'bg-primary rounded-tr-none shadow-lg shadow-blue-500/20'
                                    }`}
                            >
                                <p
                                    className={`text-xs leading-relaxed whitespace-pre-wrap ${message.role === 'assistant' ? 'text-slate-300' : 'text-white'
                                        }`}
                                >
                                    {message.content}
                                </p>
                                {message.richContent}
                            </div>
                            <span
                                className={`text-[10px] text-slate-500 ${message.role === 'user' ? 'mr-1' : 'ml-1'
                                    }`}
                            >
                                {message.timestamp}
                            </span>
                        </div>
                    </div>
                ))}

                {/* Typing Indicator */}
                {isTyping && (
                    <div className="flex gap-3">
                        <div className="size-8 rounded-lg bg-gradient-to-tr from-primary to-purple-500 flex-shrink-0 flex items-center justify-center text-white text-xs opacity-50">
                            AI
                        </div>
                        <div className="bg-slate-800/40 p-3 rounded-2xl rounded-tl-none border border-white/5 flex gap-1 items-center">
                            <div
                                className="size-1.5 rounded-full bg-slate-400 animate-bounce"
                                style={{ animationDelay: '0s' }}
                            ></div>
                            <div
                                className="size-1.5 rounded-full bg-slate-400 animate-bounce"
                                style={{ animationDelay: '0.2s' }}
                            ></div>
                            <div
                                className="size-1.5 rounded-full bg-slate-400 animate-bounce"
                                style={{ animationDelay: '0.4s' }}
                            ></div>
                        </div>
                    </div>
                )}

                {/* Error Display */}
                {error && (
                    <div className="text-red-400 text-xs text-center py-2">
                        {error}
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-white/5 bg-slate-900/40 backdrop-blur-sm">
                <form onSubmit={handleSubmit} className="relative group">
                    <input
                        type="text"
                        className="w-full bg-slate-800/50 border border-slate-700 text-slate-200 text-xs rounded-xl pl-4 pr-10 py-3 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary placeholder-slate-500 transition-all group-hover:bg-slate-800/80"
                        placeholder="Ask Veto AI..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={isTyping}
                    />
                    <button
                        type="submit"
                        className="absolute right-2 top-2 p-1 text-primary hover:text-white transition-colors rounded-lg disabled:opacity-50"
                        disabled={isTyping || !input.trim()}
                    >
                        <span className="material-symbols-outlined text-lg">send</span>
                    </button>
                </form>

            </div>
        </aside>
    );
}
