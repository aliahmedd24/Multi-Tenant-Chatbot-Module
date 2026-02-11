import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, MessageCircle } from 'lucide-react';
import { conversationsApi } from '../api';

export function ConversationsPage() {
    const navigate = useNavigate();
    const { data, isLoading } = useQuery({
        queryKey: ['conversations'],
        queryFn: () => conversationsApi.list(1, 50),
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600" />
            </div>
        );
    }

    const conversations = data?.conversations ?? [];
    const total = data?.total ?? 0;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-900">Conversations</h1>
                <p className="text-slate-500">View and manage customer conversations (channels and in-app chat)</p>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                <table className="w-full">
                    <thead className="bg-slate-50">
                        <tr>
                            <th className="text-left py-3 px-6 text-sm font-medium text-slate-500">Channel</th>
                            <th className="text-left py-3 px-6 text-sm font-medium text-slate-500">Customer</th>
                            <th className="text-right py-3 px-6 text-sm font-medium text-slate-500">Messages</th>
                            <th className="text-left py-3 px-6 text-sm font-medium text-slate-500">Status</th>
                            <th className="text-left py-3 px-6 text-sm font-medium text-slate-500">Last message</th>
                        </tr>
                    </thead>
                    <tbody>
                        {conversations.map((conv) => (
                            <tr
                                key={conv.id}
                                role="button"
                                tabIndex={0}
                                onClick={() => navigate(`/conversations/${conv.id}`)}
                                onKeyDown={(e) => e.key === 'Enter' && navigate(`/conversations/${conv.id}`)}
                                className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
                            >
                                <td className="py-4 px-6">
                                    <div className="flex items-center gap-2">
                                        {conv.channel_name === 'In-app chat' ? (
                                            <MessageCircle className="text-violet-500" size={18} />
                                        ) : (
                                            <MessageSquare className="text-slate-400" size={18} />
                                        )}
                                        <span className="font-medium text-slate-900">{conv.channel_name ?? 'Unknown'}</span>
                                    </div>
                                </td>
                                <td className="py-4 px-6">
                                    <span className="text-slate-900">{conv.customer_name || conv.customer_identifier}</span>
                                    {conv.customer_name && (
                                        <span className="text-slate-500 text-sm block">{conv.customer_identifier}</span>
                                    )}
                                </td>
                                <td className="py-4 px-6 text-right text-slate-600">{conv.message_count}</td>
                                <td className="py-4 px-6">
                                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        conv.status === 'active' ? 'bg-emerald-100 text-emerald-800' :
                                        conv.status === 'closed' ? 'bg-slate-100 text-slate-800' :
                                        'bg-amber-100 text-amber-800'
                                    }`}>
                                        {conv.status}
                                    </span>
                                </td>
                                <td className="py-4 px-6 text-slate-500 text-sm">
                                    {new Date(conv.last_message_at).toLocaleString()}
                                </td>
                            </tr>
                        ))}
                        {total === 0 && (
                            <tr>
                                <td colSpan={5} className="py-12 text-center text-slate-500">
                                    No conversations yet. Use <strong>Chat</strong> to talk to the agent, or configure WhatsApp/Instagram to receive customer messages.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
