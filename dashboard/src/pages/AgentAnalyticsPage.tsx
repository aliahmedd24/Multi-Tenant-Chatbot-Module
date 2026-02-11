import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, MessageSquare, SmilePlus, CheckCircle } from 'lucide-react';
import { agentAnalyticsApi } from '../api';
import { StatsCard } from '../components/StatsCard';
import { SentimentPieChart } from '../components/SentimentPieChart';
import { ResponseTimeGauge } from '../components/ResponseTimeGauge';
import { ResponseTimeTrendChart } from '../components/ResponseTimeTrendChart';
import { ConversationLengthChart } from '../components/ConversationLengthChart';
import { SentimentTable } from '../components/SentimentTable';
import { InsightCard } from '../components/InsightCard';

const PERIOD_OPTIONS = [
    { value: 7, label: 'Last 7 days' },
    { value: 14, label: 'Last 14 days' },
    { value: 30, label: 'Last 30 days' },
    { value: 90, label: 'Last 90 days' },
];

export function AgentAnalyticsPage() {
    const [periodDays, setPeriodDays] = useState(30);

    const { data: sentiment, isLoading: sentimentLoading } = useQuery({
        queryKey: ['agent-analytics', 'sentiment', periodDays],
        queryFn: () => agentAnalyticsApi.getSentiment(periodDays),
    });

    const { data: responseTime, isLoading: rtLoading } = useQuery({
        queryKey: ['agent-analytics', 'response-time', periodDays],
        queryFn: () => agentAnalyticsApi.getResponseTime(periodDays),
    });

    const { data: conversations, isLoading: convLoading } = useQuery({
        queryKey: ['agent-analytics', 'conversations', periodDays],
        queryFn: () => agentAnalyticsApi.getConversations(periodDays),
    });

    const { data: insights } = useQuery({
        queryKey: ['agent-analytics', 'insights', periodDays],
        queryFn: () => agentAnalyticsApi.getInsights(periodDays),
    });

    const isLoading = sentimentLoading || rtLoading || convLoading;

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Agent Analytics</h1>
                    <p className="text-slate-500">AI chatbot performance insights</p>
                </div>
                <select
                    value={periodDays}
                    onChange={(e) => setPeriodDays(Number(e.target.value))}
                    className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-violet-500"
                >
                    {PERIOD_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                <StatsCard
                    title="Avg Response Time"
                    value={`${(responseTime?.metrics.avg_response_time_seconds ?? 0).toFixed(1)}s`}
                    icon={<Clock size={24} />}
                />
                <StatsCard
                    title="Messages Analyzed"
                    value={sentiment?.total_analyzed ?? 0}
                    icon={<MessageSquare size={24} />}
                />
                <StatsCard
                    title="Sentiment Score"
                    value={`${(((sentiment?.overall_score ?? 0) + 1) / 2 * 100).toFixed(1)}%`}
                    icon={<SmilePlus size={24} />}
                />
                <StatsCard
                    title="Resolution Rate"
                    value={`${(conversations?.resolution_rate ?? 0).toFixed(1)}%`}
                    icon={<CheckCircle size={24} />}
                />
            </div>

            {/* Row 1: Response Time Trend + Sentiment Pie */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                        Response Time Trend
                    </h3>
                    <ResponseTimeTrendChart
                        data={responseTime?.daily_trend ?? []}
                        targetSeconds={responseTime?.metrics.target_seconds ?? 2}
                    />
                </div>

                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                        Sentiment Distribution
                    </h3>
                    <SentimentPieChart
                        distribution={sentiment?.distribution ?? []}
                        overallScore={sentiment?.overall_score ?? 0}
                        overallLabel={sentiment?.overall_label ?? 'neutral'}
                        satisfactionRating={sentiment?.satisfaction_rating ?? 'low'}
                    />
                </div>
            </div>

            {/* Row 2: Conversation Length + Response Time Gauge */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                        Conversation Length Distribution
                    </h3>
                    <ConversationLengthChart
                        data={conversations?.length_distribution ?? []}
                    />
                    <div className="mt-4 flex gap-6 text-sm text-slate-500">
                        <span>Avg: <strong className="text-slate-900">{conversations?.avg_message_count?.toFixed(1) ?? 0}</strong> messages</span>
                        <span>Resolved: <strong className="text-slate-900">{conversations?.resolved_count ?? 0}</strong></span>
                        <span>Handoffs: <strong className="text-slate-900">{conversations?.handoff_count ?? 0}</strong></span>
                    </div>
                </div>

                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                        Response Time Performance
                    </h3>
                    {responseTime?.metrics && (
                        <ResponseTimeGauge metrics={responseTime.metrics} />
                    )}
                </div>
            </div>

            {/* Sentiment Detail Table */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">
                    Sentiment Breakdown
                </h3>
                <SentimentTable distribution={sentiment?.distribution ?? []} />
            </div>

            {/* AI Insights */}
            {insights && insights.insights.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                        AI Insights
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {insights.insights.map((insight, idx) => (
                            <InsightCard key={idx} insight={insight} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
