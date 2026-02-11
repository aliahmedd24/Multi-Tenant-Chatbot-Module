import api from './client';
import type {
    AuthTokens,
    OverviewMetrics,
    ConversationTrends,
    MessageTrends,
    ChannelPerformance,
    Channel,
    Conversation,
    ConversationDetail,
    KnowledgeDocument,
    ChatResponse,
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

// Conversations API (channel + in-app chat)
export const conversationsApi = {
    list: async (page = 1, pageSize = 20): Promise<{ conversations: Conversation[]; total: number; page: number; page_size: number }> => {
        const response = await api.get('/conversations', {
            params: { page, page_size: pageSize },
        });
        return response.data;
    },

    get: async (id: string): Promise<ConversationDetail> => {
        const response = await api.get(`/conversations/${id}`);
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

// Chat API (POST /chat - RAG-powered agent)
export const chatApi = {
    send: async (message: string): Promise<ChatResponse> => {
        const response = await api.post<ChatResponse>('/chat', { message });
        return response.data;
    },
};

// Knowledge API (backend routes: GET/POST /knowledge/documents, DELETE /knowledge/documents/:id)
export const knowledgeApi = {
    list: async (): Promise<{ documents: KnowledgeDocument[]; total: number }> => {
        const response = await api.get('/knowledge/documents');
        return response.data;
    },

    upload: async (file: File): Promise<KnowledgeDocument> => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/knowledge/documents', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await api.delete(`/knowledge/documents/${id}`);
    },

    reprocess: async (id: string): Promise<KnowledgeDocument> => {
        const response = await api.post(`/knowledge/documents/${id}/reprocess`);
        return response.data;
    },
};
