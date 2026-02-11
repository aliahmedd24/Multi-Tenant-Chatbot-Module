import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, MessageCircle, MessageSquare, User, Bot } from 'lucide-react';
import { conversationsApi } from '../api';
import type { Message } from '../types';

function MessageBubble({ msg }: { msg: Message }) {
    const isUser = msg.direction === 'inbound';
    return (
        <div
            className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
        >
            <div
                className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${
                    isUser
                        ? 'bg-gradient-to-br from-violet-500 to-pink-500 text-white'
                        : 'bg-slate-100 text-slate-600'
                }`}
            >
                {isUser ? <User size={18} /> : <Bot size={18} />}
            </div>
            <div className={`flex-1 max-w-[85%] ${isUser ? 'text-right' : ''}`}>
                <div
                    className={`inline-block rounded-2xl px-4 py-3 text-left ${
                        isUser
                            ? 'bg-violet-600 text-white rounded-br-md'
                            : 'bg-slate-100 text-slate-900 rounded-bl-md'
                    }`}
                >
                    <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                    {new Date(msg.created_at).toLocaleString()}
                </p>
            </div>
        </div>
    );
}

export function ConversationDetailPage() {
    const { id } = useParams<{ id: string }>();
    const { data, isLoading, error } = useQuery({
        queryKey: ['conversation', id],
        queryFn: () => conversationsApi.get(id!),
        enabled: !!id,
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600" />
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="space-y-6">
                <Link
                    to="/conversations"
                    className="inline-flex items-center gap-2 text-slate-600 hover:text-violet-600"
                >
                    <ArrowLeft size={18} /> Back to conversations
                </Link>
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-amber-800">
                    Conversation not found or you don’t have access to it.
                </div>
            </div>
        );
    }

    const { messages, channel_name, customer_name, customer_identifier, status } = data;

    return (
        <div className="space-y-6 flex flex-col h-[calc(100vh-8rem)]">
            <div className="flex items-center gap-4">
                <Link
                    to="/conversations"
                    className="inline-flex items-center gap-2 text-slate-600 hover:text-violet-600"
                >
                    <ArrowLeft size={18} /> Back
                </Link>
            </div>

            <div className="flex flex-wrap items-center gap-4 pb-2 border-b border-slate-200">
                <div className="flex items-center gap-2">
                    {channel_name === 'In-app chat' ? (
                        <MessageCircle className="text-violet-500" size={20} />
                    ) : (
                        <MessageSquare className="text-slate-400" size={20} />
                    )}
                    <span className="font-semibold text-slate-900">{channel_name ?? 'Unknown'}</span>
                </div>
                <div className="text-slate-600">
                    {customer_name || customer_identifier}
                    {customer_name && (
                        <span className="text-slate-400 text-sm ml-1">({customer_identifier})</span>
                    )}
                </div>
                <span
                    className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        status === 'active'
                            ? 'bg-emerald-100 text-emerald-800'
                            : status === 'closed'
                              ? 'bg-slate-100 text-slate-800'
                              : 'bg-amber-100 text-amber-800'
                    }`}
                >
                    {status}
                </span>
            </div>

            <div className="flex-1 flex flex-col min-h-0 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center text-slate-500">
                            <p className="font-medium text-slate-700">No messages in this conversation yet.</p>
                        </div>
                    ) : (
                        messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)
                    )}
                </div>
            </div>
        </div>
    );
}
