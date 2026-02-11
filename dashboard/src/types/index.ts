// TypeScript interfaces for API responses

export interface User {
    id: string;
    email: string;
    full_name: string;
    role: string;
    tenant_id: string;
}

export interface AuthTokens {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface OverviewMetrics {
    total_conversations: number;
    total_messages: number;
    active_conversations: number;
    avg_response_time_seconds: number;
    active_channels: number;
}

export interface DailyMetric {
    date: string;
    count: number;
}

export interface ConversationTrends {
    period_days: number;
    total: number;
    daily: DailyMetric[];
}

export interface MessageTrends {
    period_days: number;
    total_inbound: number;
    total_outbound: number;
    daily_inbound: DailyMetric[];
    daily_outbound: DailyMetric[];
}

export interface Channel {
    id: string;
    tenant_id: string;
    name: string;
    channel_type: 'whatsapp' | 'instagram';
    is_active: boolean;
    phone_number_id?: string;
    instagram_page_id?: string;
    has_webhook_secret: boolean;
    last_webhook_at?: string;
    created_at: string;
    updated_at: string;
}

export interface ChannelMetrics {
    channel_id: string;
    channel_name: string;
    channel_type: string;
    conversation_count: number;
    message_count: number;
    last_message_at?: string;
}

export interface ChannelPerformance {
    channels: ChannelMetrics[];
    total_channels: number;
}

export interface Conversation {
    id: string;
    channel_id: string;
    channel_name?: string;
    customer_identifier: string;
    customer_name?: string;
    status: 'active' | 'closed' | 'handoff';
    last_message_at: string;
    message_count: number;
    created_at: string;
}

export interface Message {
    id: string;
    conversation_id: string;
    direction: 'inbound' | 'outbound';
    content: string;
    content_type: string;
    status: string;
    created_at: string;
}

export interface ConversationDetail extends Conversation {
    messages: Message[];
}

export interface KnowledgeDocument {
    id: string;
    filename: string;
    file_type: string;
    file_size?: number;
    file_size_bytes?: number;
    status: string;
    chunk_count: number;
    uploaded_at: string;
    processing_error?: string | null;
}

export interface ChatSourceDocument {
    document_id: string;
    filename: string;
    chunk_content: string;
    relevance_score: number;
}

export interface ChatUsageMetrics {
    context_chunks: number;
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
}

export interface ChatResponse {
    response: string;
    sources: ChatSourceDocument[];
    usage: ChatUsageMetrics;
}

// Agent Analytics types

export interface SentimentCount {
    sentiment: string;
    count: number;
    percentage: number;
}

export interface SentimentTrendPoint {
    date: string;
    avg_score: number;
    positive_count: number;
    negative_count: number;
    neutral_count: number;
}

export interface SentimentAnalytics {
    period_days: number;
    total_analyzed: number;
    distribution: SentimentCount[];
    overall_score: number;
    overall_label: string;
    daily_trend: SentimentTrendPoint[];
    satisfaction_rating: string;
}

export interface ResponseTimeMetrics {
    avg_response_time_seconds: number;
    min_response_time_seconds?: number;
    max_response_time_seconds?: number;
    performance_rating: string;
    target_seconds: number;
    total_responses: number;
}

export interface ResponseTimeTrendPoint {
    date: string;
    avg_seconds: number;
    count: number;
}

export interface ResponseTimeAnalytics {
    period_days: number;
    metrics: ResponseTimeMetrics;
    daily_trend: ResponseTimeTrendPoint[];
}

export interface ConversationLengthBucket {
    label: string;
    count: number;
    percentage: number;
}

export interface ConversationAnalytics {
    period_days: number;
    total_conversations: number;
    avg_message_count: number;
    resolved_count: number;
    resolution_rate: number;
    handoff_count: number;
    handoff_rate: number;
    length_distribution: ConversationLengthBucket[];
}

export interface InsightItem {
    category: string;
    severity: string;
    title: string;
    description: string;
}

export interface AgentInsights {
    insights: InsightItem[];
    generated_at: string;
}
