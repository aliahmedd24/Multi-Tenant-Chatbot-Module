import api from './client';
import type {
    AuthTokens,
    OverviewMetrics,
    ConversationTrends,
    MessageTrends,
    ChannelPerformance,
    Channel,
    Conversation,
    KnowledgeDocument,
    SentimentAnalytics,
    ResponseTimeAnalytics,
    ConversationAnalytics,
    AgentInsights,
} from '../types';

// Auth API
export const authApi = {
    login: async (email: string, password: string): Promise<AuthTokens> => {
        const response = await api.post('/auth/login', { email, password });
        return response.data;
    },

    logout: async (): Promise<void> => {
        await api.post('/auth/logout');
    },
};

// Analytics API
export const analyticsApi = {
    getOverview: async (): Promise<OverviewMetrics> => {
        const response = await api.get('/analytics/overview');
        return response.data;
    },

    getConversationTrends: async (periodDays = 30): Promise<ConversationTrends> => {
        const response = await api.get('/analytics/conversations', {
            params: { period_days: periodDays },
        });
        return response.data;
    },

    getMessageTrends: async (periodDays = 30): Promise<MessageTrends> => {
        const response = await api.get('/analytics/messages', {
            params: { period_days: periodDays },
        });
        return response.data;
    },

    getChannelPerformance: async (): Promise<ChannelPerformance> => {
        const response = await api.get('/analytics/channels');
        return response.data;
    },
};

// Channels API
export const channelsApi = {
    list: async (): Promise<{ channels: Channel[]; total: number }> => {
        const response = await api.get('/channels');
        return response.data;
    },

    get: async (id: string): Promise<Channel> => {
        const response = await api.get(`/channels/${id}`);
        return response.data;
    },

    create: async (data: Partial<Channel>): Promise<Channel> => {
        const response = await api.post('/channels', data);
        return response.data;
    },

    update: async (id: string, data: Partial<Channel>): Promise<Channel> => {
        const response = await api.patch(`/channels/${id}`, data);
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await api.delete(`/channels/${id}`);
    },
};

// Agent Analytics API
export const agentAnalyticsApi = {
    getSentiment: async (periodDays = 30): Promise<SentimentAnalytics> => {
        const response = await api.get('/analytics/agent/sentiment', {
            params: { period_days: periodDays },
        });
        return response.data;
    },

    getResponseTime: async (periodDays = 30): Promise<ResponseTimeAnalytics> => {
        const response = await api.get('/analytics/agent/response-time', {
            params: { period_days: periodDays },
        });
        return response.data;
    },

    getConversations: async (periodDays = 30): Promise<ConversationAnalytics> => {
        const response = await api.get('/analytics/agent/conversations', {
            params: { period_days: periodDays },
        });
        return response.data;
    },

    getInsights: async (periodDays = 30): Promise<AgentInsights> => {
        const response = await api.get('/analytics/agent/insights', {
            params: { period_days: periodDays },
        });
        return response.data;
    },
};

// Knowledge API
export const knowledgeApi = {
    list: async (): Promise<{ documents: KnowledgeDocument[]; total: number }> => {
        const response = await api.get('/knowledge');
        return response.data;
    },

    upload: async (file: File): Promise<KnowledgeDocument> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/knowledge/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await api.delete(`/knowledge/${id}`);
    },
};
