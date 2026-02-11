import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { SentimentCount } from '../types';

interface Props {
    distribution: SentimentCount[];
}

const sentimentColors: Record<string, string> = {
    positive: 'text-emerald-600 bg-emerald-100',
    neutral: 'text-slate-600 bg-slate-100',
    negative: 'text-red-600 bg-red-100',
};

const trendIcons: Record<string, { icon: typeof TrendingUp; color: string }> = {
    positive: { icon: TrendingUp, color: 'text-emerald-500' },
    neutral: { icon: Minus, color: 'text-slate-400' },
    negative: { icon: TrendingDown, color: 'text-red-500' },
};

export function SentimentTable({ distribution }: Props) {
    return (
        <div className="overflow-x-auto">
            <table className="w-full">
                <thead>
                    <tr className="border-b border-slate-100">
                        <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Sentiment</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Messages</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Percentage</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Trend</th>
                    </tr>
                </thead>
                <tbody>
                    {distribution.map((item) => {
                        const trend = trendIcons[item.sentiment] || trendIcons.neutral;
                        const TrendIcon = trend.icon;
                        const colorClass = sentimentColors[item.sentiment] || 'text-slate-600 bg-slate-100';

                        return (
                            <tr key={item.sentiment} className="border-b border-slate-50 hover:bg-slate-50">
                                <td className="py-3 px-4">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${colorClass}`}>
                                        {item.sentiment}
                                    </span>
                                </td>
                                <td className="py-3 px-4 text-right text-slate-600 font-medium">{item.count}</td>
                                <td className="py-3 px-4 text-right text-slate-600">{item.percentage}%</td>
                                <td className="py-3 px-4 text-right">
                                    <TrendIcon className={`inline ${trend.color}`} size={16} />
                                </td>
                            </tr>
                        );
                    })}
                    {distribution.length === 0 && (
                        <tr>
                            <td colSpan={4} className="py-8 text-center text-slate-500">
                                No sentiment data available yet
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
