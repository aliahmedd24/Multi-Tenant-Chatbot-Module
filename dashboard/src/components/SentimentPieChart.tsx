import {
    PieChart,
    Pie,
    Cell,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';
import type { SentimentCount } from '../types';

const COLORS: Record<string, string> = {
    positive: '#10b981',
    neutral: '#64748b',
    negative: '#ef4444',
};

interface Props {
    distribution: SentimentCount[];
    overallScore: number;
    overallLabel: string;
    satisfactionRating: string;
}

export function SentimentPieChart({ distribution, overallScore, overallLabel, satisfactionRating }: Props) {
    const ratingConfig: Record<string, { label: string; color: string }> = {
        high: { label: 'High', color: 'text-emerald-600' },
        moderate: { label: 'Moderate', color: 'text-amber-600' },
        low: { label: 'Low', color: 'text-red-600' },
    };

    const rating = ratingConfig[satisfactionRating] || ratingConfig.low;
    const scorePct = ((overallScore + 1) / 2 * 100).toFixed(1);

    return (
        <div>
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={distribution}
                            dataKey="count"
                            nameKey="sentiment"
                            cx="50%"
                            cy="50%"
                            outerRadius={90}
                            innerRadius={50}
                            paddingAngle={2}
                            label={({ sentiment, percentage }) => `${sentiment} ${percentage}%`}
                        >
                            {distribution.map((entry) => (
                                <Cell
                                    key={entry.sentiment}
                                    fill={COLORS[entry.sentiment] || '#94a3b8'}
                                />
                            ))}
                        </Pie>
                        <Tooltip
                            formatter={(value: number, name: string) => [`${value} messages`, name]}
                            contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }}
                        />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                <div>
                    <p className="text-sm text-slate-500">Overall Score</p>
                    <p className="text-2xl font-bold text-violet-600">{scorePct}%</p>
                </div>
                <div>
                    <p className="text-sm text-slate-500">Sentiment</p>
                    <p className="text-lg font-semibold capitalize">{overallLabel}</p>
                </div>
                <div>
                    <p className="text-sm text-slate-500">Satisfaction</p>
                    <p className={`text-lg font-semibold ${rating.color}`}>{rating.label}</p>
                </div>
            </div>
        </div>
    );
}
