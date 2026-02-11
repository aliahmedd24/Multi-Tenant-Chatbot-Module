import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from 'recharts';
import type { ConversationLengthBucket } from '../types';

interface Props {
    data: ConversationLengthBucket[];
}

export function ConversationLengthChart({ data }: Props) {
    return (
        <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                        dataKey="label"
                        tick={{ fontSize: 12 }}
                        label={{ value: 'Messages per conversation', position: 'insideBottom', offset: -5, style: { fontSize: 12 } }}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                        contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }}
                        formatter={(value: number, _name: string, props: { payload: ConversationLengthBucket }) => [
                            `${value} conversations (${props.payload.percentage}%)`,
                            'Count',
                        ]}
                    />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
