import { useRef, useEffect, useState } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { chatApi } from '../api';
import type { ChatSourceDocument } from '../types';

type MessageRole = 'user' | 'assistant';

interface ChatMessage {
    id: string;
    role: MessageRole;
    content: string;
    sources?: ChatSourceDocument[];
    usage?: { context_chunks: number; total_tokens?: number };
    timestamp: Date;
}

export function ChatPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const text = input.trim();
        if (!text || isLoading) return;

        setInput('');
        const userMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'user',
            content: text,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const res = await chatApi.send(text);
            const assistantMessage: ChatMessage = {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: res.response,
                sources: res.sources?.length ? res.sources : undefined,
                usage: res.usage,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (err) {
            const detail =
                err && typeof err === 'object' && 'response' in err
                    ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
                    : null;
            setMessages((prev) => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: detail
                        ? `Error: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`
                        : 'Something went wrong. Please try again.',
                    timestamp: new Date(),
                },
            ]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    return (
        <div className="space-y-6 flex flex-col h-[calc(100vh-8rem)]">
            <div>
                <h1 className="text-2xl font-bold text-slate-900">Chat</h1>
                <p className="text-slate-500">Talk to your AI agent in real time</p>
            </div>

            <div className="flex-1 flex flex-col min-h-0 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-center text-slate-500">
                            <div className="inline-flex justify-center w-14 h-14 rounded-full bg-violet-100 mb-4">
                                <Bot className="text-violet-600" size={28} />
                            </div>
                            <p className="font-medium text-slate-700">Start a conversation</p>
                            <p className="text-sm mt-1 max-w-sm">
                                Ask anything about your knowledge base. Responses use your uploaded documents.
                            </p>
                        </div>
                    )}
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div
                                className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${
                                    msg.role === 'user'
                                        ? 'bg-gradient-to-br from-violet-500 to-pink-500 text-white'
                                        : 'bg-slate-100 text-slate-600'
                                }`}
                            >
                                {msg.role === 'user' ? (
                                    <User size={18} />
                                ) : (
                                    <Bot size={18} />
                                )}
                            </div>
                            <div
                                className={`flex-1 max-w-[85%] ${msg.role === 'user' ? 'text-right' : ''}`}
                            >
                                <div
                                    className={`inline-block rounded-2xl px-4 py-3 text-left ${
                                        msg.role === 'user'
                                            ? 'bg-violet-600 text-white rounded-br-md'
                                            : 'bg-slate-100 text-slate-900 rounded-bl-md'
                                    }`}
                                >
                                    <p className="text-sm whitespace-pre-wrap break-words">
                                        {msg.content}
                                    </p>
                                </div>
                                {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                                    <details className="mt-2 text-left">
                                        <summary className="text-xs text-slate-500 cursor-pointer hover:text-violet-600">
                                            {msg.sources.length} source(s)
                                        </summary>
                                        <ul className="mt-1 space-y-1 text-xs text-slate-600">
                                            {msg.sources.map((s, i) => (
                                                <li key={i} className="border-l-2 border-violet-200 pl-2">
                                                    <span className="font-medium">{s.filename}</span>
                                                    {s.relevance_score != null && (
                                                        <span className="text-slate-400 ml-1">
                                                            ({(s.relevance_score * 100).toFixed(0)}%)
                                                        </span>
                                                    )}
                                                </li>
                                            ))}
                                        </ul>
                                    </details>
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex gap-3">
                            <div className="flex-shrink-0 w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                                <Bot size={18} />
                            </div>
                            <div className="rounded-2xl rounded-bl-md bg-slate-100 px-4 py-3">
                                <Loader2 size={20} className="animate-spin text-violet-600" />
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <form
                    onSubmit={handleSubmit}
                    className="p-4 border-t border-slate-100 bg-slate-50/50"
                >
                    <div className="flex gap-3">
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e);
                                }
                            }}
                            placeholder="Type your message..."
                            rows={1}
                            disabled={isLoading}
                            className="flex-1 resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20 disabled:opacity-50"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isLoading}
                            className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-xl bg-violet-600 text-white hover:bg-violet-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <Loader2 size={20} className="animate-spin" />
                            ) : (
                                <Send size={20} />
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
