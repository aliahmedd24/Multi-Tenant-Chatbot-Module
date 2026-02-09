import { useQuery } from '@tanstack/react-query';
import {
    MessageSquare,
    Users,
    Radio,
    Clock
} from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
} from 'recharts';
import { analyticsApi } from '../api';
import { StatsCard } from '../components/StatsCard';

export function DashboardPage() {
    const { data: overview, isLoading: overviewLoading } = useQuery({
        queryKey: ['analytics', 'overview'],
        queryFn: analyticsApi.getOverview,
    });

    const { data: conversationTrends } = useQuery({
        queryKey: ['analytics', 'conversations'],
        queryFn: () => analyticsApi.getConversationTrends(30),
    });

    const { data: messageTrends } = useQuery({
        queryKey: ['analytics', 'messages'],
        queryFn: () => analyticsApi.getMessageTrends(30),
    });

    const { data: channelPerformance } = useQuery({
        queryKey: ['analytics', 'channels'],
        queryFn: analyticsApi.getChannelPerformance,
    });

    if (overviewLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
                <p className="text-slate-500">Overview of your AI concierge performance</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                <StatsCard
                    title="Total Conversations"
                    value={overview?.total_conversations ?? 0}
                    icon={<MessageSquare size={24} />}
                />
                <StatsCard
                    title="Total Messages"
                    value={overview?.total_messages ?? 0}
                    icon={<Users size={24} />}
                />
                <StatsCard
                    title="Active Channels"
                    value={overview?.active_channels ?? 0}
                    icon={<Radio size={24} />}
                />
                <StatsCard
                    title="Avg Response Time"
                    value={`${(overview?.avg_response_time_seconds ?? 0).toFixed(1)}s`}
                    icon={<Clock size={24} />}
                />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Conversation Trends */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                        Conversations (Last 30 Days)
                    </h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={conversationTrends?.daily ?? []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 12 }}
                                    tickFormatter={(val) => new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                />
                                <YAxis tick={{ fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }}
                                    labelFormatter={(val) => new Date(val).toLocaleDateString()}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="count"
                                    stroke="#8b5cf6"
                                    strokeWidth={2}
                                    dot={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Message Volume */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                        Message Volume
                    </h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={messageTrends?.daily_inbound ?? []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 12 }}
                                    tickFormatter={(val) => new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                />
                                <YAxis tick={{ fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }}
                                    labelFormatter={(val) => new Date(val).toLocaleDateString()}
                                />
                                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Channel Performance */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">
                    Channel Performance
                </h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-100">
                                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Channel</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Type</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Conversations</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Messages</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Last Active</th>
                            </tr>
                        </thead>
                        <tbody>
                            {channelPerformance?.channels.map((channel) => (
                                <tr key={channel.channel_id} className="border-b border-slate-50 hover:bg-slate-50">
                                    <td className="py-3 px-4 font-medium text-slate-900">{channel.channel_name}</td>
                                    <td className="py-3 px-4">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${channel.channel_type === 'whatsapp'
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-pink-100 text-pink-800'
                                            }`}>
                                            {channel.channel_type}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-right text-slate-600">{channel.conversation_count}</td>
                                    <td className="py-3 px-4 text-right text-slate-600">{channel.message_count}</td>
                                    <td className="py-3 px-4 text-right text-slate-500 text-sm">
                                        {channel.last_message_at
                                            ? new Date(channel.last_message_at).toLocaleDateString()
                                            : '—'
                                        }
                                    </td>
                                </tr>
                            ))}
                            {(channelPerformance?.channels.length ?? 0) === 0 && (
                                <tr>
                                    <td colSpan={5} className="py-8 text-center text-slate-500">
                                        No channels configured yet
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
