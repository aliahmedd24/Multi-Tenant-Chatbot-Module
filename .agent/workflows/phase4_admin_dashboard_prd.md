---
description: # Phase 4: Admin Dashboard & Analytics | ## Objective Build a web-based admin dashboard for tenant administrators to monitor chatbot performance, view conversations, manage knowledge base, configure channels, and analyze key metrics. This phase provi
---

## Tech Stack
- **Frontend Framework**: React 18 with TypeScript
- **UI Library**: Tailwind CSS + shadcn/ui components
- **State Management**: TanStack Query (React Query) for server state
- **Routing**: React Router v6
- **Charts**: Recharts or Chart.js
- **Data Tables**: TanStack Table (React Table)
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios
- **Real-time Updates**: WebSockets (Socket.io) for live message notifications
- **Authentication**: JWT stored in httpOnly cookies
- **Build Tool**: Vite
- **Testing**: Vitest + React Testing Library

## User Flow

### Initial Login
1. User navigates to `https://admin.wafaa.ai`
2. User enters email and password
3. System authenticates and returns JWT tokens
4. User redirected to Dashboard Overview page

### Dashboard Navigation
1. **Overview Page**: High-level metrics (messages today, active conversations, response time)
2. **Conversations Tab**: List of all conversations with search/filter
3. **Knowledge Base Tab**: Document management interface
4. **Channels Tab**: Connected channels with connection status
5. **Configuration Tab**: Bot personality, custom instructions, business info
6. **Analytics Tab**: Charts and reports (messages over time, topics, sentiment)
7. **Settings Tab**: Admin management, billing, API keys

### Conversation Management Flow
1. User clicks "Conversations" tab
2. System loads paginated list of conversations (20 per page)
3. User applies filters (date range, status, channel)
4. User clicks on specific conversation to view details
5. Right panel shows full message history with timestamps
6. User can see customer info (name, phone/handle, first message date)
7. User can manually send message (Phase 5 human takeover)
8. User marks conversation as "Resolved"

### Knowledge Base Management Flow
1. User clicks "Knowledge Base" tab
2. System shows list of uploaded documents with status badges
3. User clicks "Upload Document" button
4. User selects file (PDF/DOCX/CSV) and adds description
5. Upload progress bar shows processing status
6. Document appears in list with "Processing" status
7. Status changes to "Ready" when complete (or "Failed" with error)
8. User can download, preview, or delete documents

### Channel Connection Flow
1. User clicks "Channels" tab
2. System shows grid of available channels (WhatsApp, Instagram, TikTok, Snapchat)
3. User clicks "Connect" on WhatsApp card
4. Modal explains permissions needed
5. User clicks "Authorize" → redirects to Meta OAuth
6. User grants permissions
7. System redirects back with success message
8. WhatsApp card shows "Connected" badge with phone number
9. User can test connection by sending test message

## Technical Constraints
- **Mobile Responsive**: Must work on tablets and phones (min-width: 320px)
- **Accessibility**: WCAG 2.1 Level AA compliance (keyboard navigation, ARIA labels)
- **Performance**: Initial load < 3s, route transitions < 500ms
- **Browser Support**: Last 2 versions of Chrome, Firefox, Safari, Edge
- **API Rate Limits**: Dashboard must handle 429 errors gracefully
- **Real-time Updates**: Live conversation updates when new messages arrive
- **Offline Handling**: Show connection status; queue actions when offline
- **No External CDNs**: All assets self-hosted for security

## Data Schema (Frontend Models)

### Dashboard Metrics
```typescript
interface DashboardMetrics {
    messagesTotal: number;
    messagesToday: number;
    activeConversations: number;
    averageResponseTimeSeconds: number;
    totalDocuments: number;
    connectedChannels: number;
    period: {
        start: string; // ISO datetime
        end: string;
    }
}
```

### Conversation List Item
```typescript
interface ConversationListItem {
    id: string;
    customerName: string | null;
    customerIdentifier: string; // phone or handle
    channelType: 'whatsapp' | 'instagram' | 'tiktok' | 'snapchat';
    lastMessagePreview: string;
    lastMessageAt: string; // ISO datetime
    status: 'active' | 'resolved' | 'expired';
    messageCount: number;
    unreadCount: number; // Phase 5
}
```

### Conversation Detail
```typescript
interface ConversationDetail {
    id: string;
    sessionId: string;
    customer: {
        identifier: string;
        name: string | null;
        avatarUrl: string | null;
    };
    channel: {
        type: 'whatsapp' | 'instagram' | 'tiktok' | 'snapchat';
        name: string;
    };
    startedAt: string;
    lastMessageAt: string;
    status: 'active' | 'resolved' | 'expired';
    messages: Message[];
}

interface Message {
    id: string;
    direction: 'inbound' | 'outbound';
    content: string;
    contentType: 'text' | 'image' | 'video' | 'audio' | 'document';
    senderRole: 'customer' | 'bot' | 'human_agent';
    timestamp: string;
    status: 'sent' | 'delivered' | 'read' | 'failed';
    metadata?: {
        ragContext?: string[];
        tokensUsed?: number;
        confidence?: number;
    };
}
```

### Knowledge Document
```typescript
interface KnowledgeDocument {
    id: string;
    filename: string;
    fileType: 'pdf' | 'docx' | 'txt' | 'csv' | 'json';
    fileSizeBytes: number;
    status: 'uploading' | 'processing' | 'ready' | 'failed';
    processingError: string | null;
    uploadedBy: string; // admin name
    uploadedAt: string;
    processedAt: string | null;
    chunkCount: number;
    metadata: {
        category?: string;
        description?: string;
    };
}
```

### Connected Channel
```typescript
interface ConnectedChannel {
    id: string;
    channelType: 'whatsapp' | 'instagram' | 'tiktok' | 'snapchat';
    channelId: string; // phone or page ID
    channelName: string;
    status: 'active' | 'error' | 'disconnected';
    webhookVerified: boolean;
    lastSync: string | null;
    metadata: {
        phoneNumber?: string;
        pageId?: string;
        displayName?: string;
    };
    connectedAt: string;
}
```

### Tenant Configuration
```typescript
interface TenantConfiguration {
    businessName: string;
    businessHours: {
        [key: string]: { // e.g., "monday", "tuesday"
            open: string; // "09:00"
            close: string; // "17:00"
        };
    };
    address: string;
    phone: string;
    email: string;
    website: string | null;
    customInstructions: string;
    tone: 'formal' | 'casual' | 'friendly' | 'professional';
    responseLanguage: string; // ISO code
    allowedTopics: string[];
    blockedTopics: string[];
}
```

### Analytics Data
```typescript
interface MessagesOverTime {
    date: string; // YYYY-MM-DD
    inbound: number;
    outbound: number;
}

interface TopicBreakdown {
    topic: string;
    count: number;
    percentage: number;
}

interface ChannelPerformance {
    channelType: string;
    messageCount: number;
    averageResponseTime: number;
    resolutionRate: number;
}
```

## Page Structure

### 1. Dashboard Overview (`/dashboard`)
**Components:**
- Metrics Cards: Messages today, active conversations, avg response time
- Recent Conversations List (last 10)
- Quick Actions: Upload document, connect channel, view analytics
- Activity Feed: Recent events (new connection, document uploaded, etc.)

**API Calls:**
- `GET /api/v1/analytics/dashboard` → DashboardMetrics
- `GET /api/v1/conversations?limit=10` → ConversationListItem[]

### 2. Conversations Page (`/conversations`)
**Components:**
- Search Bar: Filter by customer name/identifier
- Filter Dropdown: Channel, status, date range
- Conversations Table: Sortable columns (last message, status)
- Pagination Controls

**Conversation Detail Modal:**
- Customer Info Panel (left)
- Message Thread (center)
- Action Buttons: Mark resolved, handoff to human (Phase 5)

**API Calls:**
- `GET /api/v1/conversations?page=1&limit=20&status=active`
- `GET /api/v1/conversations/{id}` → ConversationDetail
- `PATCH /api/v1/conversations/{id}` → Update status

### 3. Knowledge Base Page (`/knowledge`)
**Components:**
- Upload Button with drag-and-drop zone
- Documents Table: Filename, type, size, status, actions
- Document Preview Modal (for text files)
- Delete Confirmation Dialog

**API Calls:**
- `GET /api/v1/knowledge/documents`
- `POST /api/v1/knowledge/documents` (multipart form)
- `DELETE /api/v1/knowledge/documents/{id}`
- `GET /api/v1/knowledge/documents/{id}/chunks` (preview)

### 4. Channels Page (`/channels`)
**Components:**
- Channel Cards Grid: WhatsApp, Instagram, TikTok, Snapchat
- Connection Status Badge: Connected, Disconnected, Error
- Test Connection Button
- Disconnect Button with confirmation

**API Calls:**
- `GET /api/v1/channels`
- `POST /api/v1/channels/whatsapp/connect` → Redirect URL
- `DELETE /api/v1/channels/{id}`
- `POST /api/v1/channels/{id}/test`

### 5. Configuration Page (`/config`)
**Components:**
- Business Info Form: Name, hours, address, contact
- Bot Personality Section: Tone selector, custom instructions
- Language Settings: Response language, allowed/blocked topics
- Save/Cancel Buttons

**API Calls:**
- `GET /api/v1/config` → TenantConfiguration
- `PUT /api/v1/config`
- `POST /api/v1/config/validate`

### 6. Analytics Page (`/analytics`)
**Components:**
- Date Range Picker
- Line Chart: Messages over time (inbound vs outbound)
- Bar Chart: Top topics discussed
- Pie Chart: Channel distribution
- Table: Channel performance metrics

**API Calls:**
- `GET /api/v1/analytics/messages/count?start_date=X&end_date=Y`
- `GET /api/v1/analytics/topics?limit=10`
- `GET /api/v1/analytics/channels/performance`

### 7. Settings Page (`/settings`)
**Components:**
- Admin Management: List of admins, add/remove
- API Keys: Generate, view, revoke (Phase 5)
- Billing: Current plan, usage limits (Phase 5)
- Account: Change password, logout

**API Calls:**
- `GET /api/v1/tenants/me/admins`
- `POST /api/v1/tenants/me/admins`
- `DELETE /api/v1/tenants/me/admins/{id}`

## Directory Structure
```
wafaa-dashboard/
├── public/
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts (axios instance)
│   │   ├── auth.ts
│   │   ├── conversations.ts
│   │   ├── knowledge.ts
│   │   ├── channels.ts
│   │   ├── config.ts
│   │   └── analytics.ts
│   ├── components/
│   │   ├── ui/ (shadcn components)
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   ├── conversations/
│   │   │   ├── ConversationList.tsx
│   │   │   ├── ConversationDetail.tsx
│   │   │   └── MessageBubble.tsx
│   │   ├── knowledge/
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentTable.tsx
│   │   │   └── DocumentPreview.tsx
│   │   ├── channels/
│   │   │   ├── ChannelCard.tsx
│   │   │   └── ConnectChannelModal.tsx
│   │   ├── analytics/
│   │   │   ├── MessagesChart.tsx
│   │   │   ├── TopicsChart.tsx
│   │   │   └── ChannelPerformance.tsx
│   │   └── common/
│   │       ├── MetricCard.tsx
│   │       ├── StatusBadge.tsx
│   │       └── LoadingSpinner.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ConversationsPage.tsx
│   │   ├── KnowledgePage.tsx
│   │   ├── ChannelsPage.tsx
│   │   ├── ConfigPage.tsx
│   │   ├── AnalyticsPage.tsx
│   │   └── SettingsPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useConversations.ts
│   │   ├── useKnowledge.ts
│   │   ├── useChannels.ts
│   │   └── useWebSocket.ts
│   ├── context/
│   │   └── AuthContext.tsx
│   ├── types/
│   │   ├── api.ts (API response types)
│   │   └── models.ts (data models)
│   ├── utils/
│   │   ├── formatDate.ts
│   │   ├── formatFileSize.ts
│   │   └── constants.ts
│   └── styles/
│       └── globals.css
├── .env.example
├── .gitignore
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Key Features Implementation

### Real-time Message Updates
```typescript
// useWebSocket.ts
export function useWebSocket() {
    const socket = useRef<Socket>();
    
    useEffect(() => {
        socket.current = io('ws://localhost:8000', {
            auth: { token: getAuthToken() }
        });
        
        socket.current.on('new_message', (message: Message) => {
            // Update conversation in React Query cache
            queryClient.setQueryData(['conversation', message.conversationId], 
                (old: ConversationDetail) => ({
                    ...old,
                    messages: [...old.messages, message]
                })
            );
            
            // Show notification
            toast.info(`New message from ${message.customerName}`);
        });
        
        return () => socket.current?.disconnect();
    }, []);
}
```

### Document Upload with Progress
```typescript
// DocumentUpload.tsx
const uploadDocument = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify({
        category: selectedCategory,
        description: description
    }));
    
    await axios.post('/api/v1/knowledge/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total!
            );
            setUploadProgress(percentCompleted);
        }
    });
};
```

### Conversation Filters
```typescript
// ConversationsPage.tsx
const [filters, setFilters] = useState({
    search: '',
    channel: 'all',
    status: 'all',
    dateRange: { start: null, end: null }
});

const { data: conversations } = useQuery({
    queryKey: ['conversations', filters],
    queryFn: () => api.conversations.list({
        search: filters.search,
        channel_type: filters.channel !== 'all' ? filters.channel : undefined,
        status: filters.status !== 'all' ? filters.status : undefined,
        start_date: filters.dateRange.start,
        end_date: filters.dateRange.end
    })
});
```

## Environment Variables
```
# API
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000

# OAuth (for redirect URIs)
VITE_WHATSAPP_REDIRECT_URI=http://localhost:5173/auth/callback/whatsapp
VITE_INSTAGRAM_REDIRECT_URI=http://localhost:5173/auth/callback/instagram

# Feature Flags (Phase 5+)
VITE_ENABLE_HUMAN_HANDOFF=false
VITE_ENABLE_BILLING=false
```

## Definition of Done

### Code Requirements
- [ ] All pages render without errors
- [ ] Authentication guards protect private routes
- [ ] JWT refresh logic implemented (auto-refresh before expiry)
- [ ] All forms validate input with Zod schemas
- [ ] API errors display user-friendly messages
- [ ] Loading states shown for all async operations
- [ ] Empty states designed for zero-data scenarios
- [ ] 404 page for invalid routes

### Testing Requirements
- [ ] Unit tests for all custom hooks (80%+ coverage)
- [ ] Component tests for critical UI (login, upload, message display)
- [ ] Integration test: login → view conversations → open detail
- [ ] Test responsive design on mobile viewport (375px)
- [ ] Test keyboard navigation (tab through forms)
- [ ] Test screen reader compatibility (NVDA/VoiceOver)
- [ ] Test API error handling (network failure, 401, 500)
- [ ] Test WebSocket reconnection on disconnect

### Functional Requirements
- [ ] User can log in and see dashboard metrics
- [ ] User can view paginated list of conversations
- [ ] User can open conversation and see all messages
- [ ] User can search conversations by customer name
- [ ] User can filter conversations by channel/status
- [ ] User can upload PDF document successfully
- [ ] Upload progress bar updates in real-time
- [ ] User can see document processing status
- [ ] User can delete document with confirmation
- [ ] User can connect WhatsApp via OAuth
- [ ] Connected channels show green "Active" badge
- [ ] User can update bot configuration and save
- [ ] Configuration form validates required fields
- [ ] User can view messages-over-time chart
- [ ] Chart updates when date range changes
- [ ] User can manage admins (add/remove)
- [ ] User can log out and token is invalidated

### Performance Requirements
- [ ] Initial page load < 3 seconds on 4G connection
- [ ] Route transitions < 500ms
- [ ] Conversations list renders 100 items without lag
- [ ] Message thread renders 500 messages smoothly
- [ ] Chart renders 90 days of data in < 1 second
- [ ] WebSocket reconnects within 5 seconds of disconnect

### Accessibility Requirements
- [ ] All interactive elements keyboard-accessible
- [ ] Focus indicators visible on all inputs
- [ ] ARIA labels on icon-only buttons
- [ ] Form errors announced to screen readers
- [ ] Color contrast ratios meet WCAG AA (4.5:1 for text)
- [ ] No flashing animations (epilepsy risk)

### Security Requirements
- [ ] JWT stored in httpOnly cookie (not localStorage)
- [ ] CSRF token included in state-changing requests
- [ ] Input sanitized to prevent XSS
- [ ] No sensitive data in console.log statements
- [ ] Logout invalidates token on server
- [ ] Session expires after 30 minutes of inactivity

### Documentation Requirements
- [ ] README includes setup instructions
- [ ] Component usage documented with JSDoc
- [ ] API client methods documented
- [ ] .env.example provided
- [ ] Storybook setup for UI components (optional)

## Success Metrics
- 90%+ of users complete login on first attempt
- 95%+ of document uploads succeed
- Average time to connect channel: < 2 minutes
- User can find specific conversation in < 10 seconds
- Dashboard loads in < 2 seconds for 95% of users
- Zero critical accessibility violations (axe DevTools)

## Next Phase Dependencies
Phase 5 (Human Handoff) requires:
- Conversation detail view from this phase
- Real-time message updates via WebSocket
- Manual message sending UI (already in conversation detail)
- Admin role permissions for handoff feature
