import { AlertTriangle, CheckCircle, Info } from 'lucide-react';
import type { InsightItem } from '../types';

interface Props {
    insight: InsightItem;
}

const severityConfig: Record<string, { icon: typeof Info; color: string; bg: string; border: string }> = {
    info: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100' },
    warning: { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100' },
    success: { icon: CheckCircle, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100' },
};

export function InsightCard({ insight }: Props) {
    const config = severityConfig[insight.severity] || severityConfig.info;
    const Icon = config.icon;

    return (
        <div className={`rounded-xl p-4 ${config.bg} border ${config.border}`}>
            <div className="flex items-start gap-3">
                <Icon className={`${config.color} mt-0.5 flex-shrink-0`} size={20} />
                <div>
                    <p className={`font-semibold ${config.color}`}>{insight.title}</p>
                    <p className="text-sm text-slate-600 mt-1">{insight.description}</p>
                    <span className="inline-block mt-2 text-xs text-slate-400 capitalize">{insight.category}</span>
                </div>
            </div>
        </div>
    );
}
