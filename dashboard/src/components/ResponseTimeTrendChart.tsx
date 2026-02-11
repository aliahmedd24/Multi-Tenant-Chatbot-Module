import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    ResponsiveContainer,
} from 'recharts';
import type { ResponseTimeTrendPoint } from '../types';

interface Props {
    data: ResponseTimeTrendPoint[];
    targetSeconds: number;
}

export function ResponseTimeTrendChart({ data, targetSeconds }: Props) {
    return (
        <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(val) =>
                            new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                        }
                    />
                    <YAxis
                        tick={{ fontSize: 12 }}
                        label={{ value: 'Seconds', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                    />
                    <Tooltip
                        contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }}
                        labelFormatter={(val) => new Date(val).toLocaleDateString()}
                        formatter={(value: number) => [`${value.toFixed(2)}s`, 'Avg Response Time']}
                    />
                    <ReferenceLine
                        y={targetSeconds}
                        stroke="#10b981"
                        strokeDasharray="6 4"
                        label={{ value: `${targetSeconds}s target`, position: 'right', fontSize: 11, fill: '#10b981' }}
                    />
                    <Line
                        type="monotone"
                        dataKey="avg_seconds"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        dot={{ fill: '#8b5cf6', r: 3 }}
                        activeDot={{ r: 5 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
