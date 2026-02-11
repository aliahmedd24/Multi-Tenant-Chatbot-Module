import type { ResponseTimeMetrics } from '../types';

interface Props {
    metrics: ResponseTimeMetrics;
}

export function ResponseTimeGauge({ metrics }: Props) {
    const { avg_response_time_seconds, performance_rating, target_seconds, total_responses } = metrics;

    const ratingConfig: Record<string, { label: string; color: string; bgColor: string }> = {
        excellent: { label: 'Excellent', color: 'text-emerald-600', bgColor: 'bg-emerald-500' },
        good: { label: 'Good', color: 'text-amber-600', bgColor: 'bg-amber-500' },
        needs_improvement: { label: 'Needs Improvement', color: 'text-red-600', bgColor: 'bg-red-500' },
    };

    const rating = ratingConfig[performance_rating] || ratingConfig.needs_improvement;

    // Gauge bar: scale 0-10s, clamped
    const maxScale = 10;
    const fillPct = Math.min((avg_response_time_seconds / maxScale) * 100, 100);

    return (
        <div className="space-y-6">
            <div className="text-center">
                <p className="text-4xl font-bold text-slate-900">
                    {avg_response_time_seconds.toFixed(1)}s
                </p>
                <p className="text-sm text-slate-500 mt-1">Average Response Time</p>
            </div>

            {/* Gauge bar */}
            <div>
                <div className="relative h-4 bg-slate-100 rounded-full overflow-hidden">
                    {/* Threshold zones */}
                    <div className="absolute inset-y-0 left-0 bg-emerald-200 rounded-l-full" style={{ width: `${(target_seconds / maxScale) * 100}%` }} />
                    <div className="absolute inset-y-0 bg-amber-200" style={{ left: `${(target_seconds / maxScale) * 100}%`, width: `${(3 / maxScale) * 100}%` }} />
                    <div className="absolute inset-y-0 bg-red-200 rounded-r-full" style={{ left: `${(5 / maxScale) * 100}%`, right: 0 }} />
                    {/* Current value indicator */}
                    <div
                        className={`absolute inset-y-0 left-0 ${rating.bgColor} rounded-full opacity-80 transition-all duration-500`}
                        style={{ width: `${fillPct}%` }}
                    />
                </div>
                <div className="flex justify-between mt-1 text-xs text-slate-400">
                    <span>0s</span>
                    <span>{target_seconds}s target</span>
                    <span>5s</span>
                    <span>{maxScale}s</span>
                </div>
            </div>

            {/* Rating and stats */}
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-slate-500">Performance Rating</p>
                    <p className={`text-lg font-semibold ${rating.color}`}>{rating.label}</p>
                </div>
                <div className="text-right">
                    <p className="text-sm text-slate-500">Total Responses</p>
                    <p className="text-lg font-semibold text-slate-900">{total_responses}</p>
                </div>
            </div>

            {/* Threshold legend */}
            <div className="flex gap-4 text-xs text-slate-500">
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded-full bg-emerald-400" />
                    Target: &lt;{target_seconds}s
                </div>
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded-full bg-amber-400" />
                    Good: {target_seconds}-5s
                </div>
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded-full bg-red-400" />
                    Slow: &gt;5s
                </div>
            </div>
        </div>
    );
}
