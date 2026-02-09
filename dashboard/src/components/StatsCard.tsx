import { ReactNode } from 'react';
import { clsx } from 'clsx';

interface StatsCardProps {
    title: string;
    value: string | number;
    icon: ReactNode;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    className?: string;
}

export function StatsCard({ title, value, icon, trend, className }: StatsCardProps) {
    return (
        <div
            className={clsx(
                'bg-white rounded-2xl p-6 shadow-sm border border-slate-100',
                className
            )}
        >
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-slate-500 text-sm font-medium">{title}</p>
                    <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
                    {trend && (
                        <p
                            className={clsx(
                                'mt-2 text-sm font-medium',
                                trend.isPositive ? 'text-emerald-600' : 'text-red-600'
                            )}
                        >
                            {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
                        </p>
                    )}
                </div>
                <div className="p-3 bg-gradient-to-br from-violet-500 to-pink-500 rounded-xl text-white">
                    {icon}
                </div>
            </div>
        </div>
    );
}
