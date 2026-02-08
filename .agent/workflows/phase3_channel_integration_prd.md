---
description: # Phase 3: Channel Integration - WhatsApp & Instagram | ## Objective Integrate WhatsApp Business API and Instagram Direct Messages to receive and respond to customer inquiries automatically. This phase connects external messaging platforms to the RAG
---

## Tech Stack
- **WhatsApp**: Meta Cloud API or Twilio API for WhatsApp Business
- **Instagram**: Meta Graph API (requires Facebook Business account)
- **Webhook Framework**: FastAPI endpoints for receiving messages
- **Message Queue**: Redis Streams for message processing pipeline
- **Session Management**: Redis with TTL for conversation state
- **OAuth 2.0**: requests-oauthlib for Facebook/Meta authentication
- **Webhook Validation**: cryptography library for signature verification
- **Rate Limiting**: slowapi (FastAPI rate limiter)
- **HTTP Client**: httpx for async API calls
- **Background Processing**: Celery (from Phase 2) for async message handling

## User Flow

### Tenant Onboarding Flow
1. Tenant admin navigates to "Connect Channels" section
2. Admin clicks "Connect WhatsApp" button
3. System redirects to Meta Business login (OAuth flow)
4. Admin grants permissions for message management
5. System stores access token encrypted in database
6. Admin selects which WhatsApp number to connect (from Meta Business account)
7. System configures webhook URL with Meta API
8. Connection status changes to "Connected" with green indicator
9. Admin repeats process for Instagram (connects Instagram Business account)
10. Admin tests connection by sending test message to their number
11. System receives message, generates response, and replies

### Customer Interaction Flow
1. Customer sends message to Restaurant A's WhatsApp number
2. Meta forwards message to Wafaa webhook: `POST /webhooks/whatsapp`
3. Wafaa identifies tenant by phone number mapping
4. System retrieves or creates session for this customer-tenant conversation
5. Message sent to Celery queue for async processing
6. Worker retrieves tenant's knowledge base and configuration
7. RAG engine generates contextual response
8. System calls Meta API to send response back to customer
9. Conversation stored in database with tenant_id + session_id
10. Process repeats for subsequent messages in conversation

## Technical Constraints
- **Message Ordering**: Must preserve message sequence per conversation
- **Response Time**: Reply to customer within 10 seconds (Meta requirement)
- **Webhook Security**: All webhooks must validate signature from Meta
- **Rate Limits**: Respect Meta API limits (80 messages/second per phone number)
- **Session TTL**: Conversations expire after 24 hours of inactivity
- **Media Handling**: Phase 3 supports text only; media planned for Phase 4
- **Error Recovery**: Failed message sends must retry 3 times with exponential backoff
- **Duplicate Prevention**: Idempotency keys prevent processing same message twice
- **Compliance**: Must handle opt-out/stop requests immediately

## Data Schema

### Connected Channels Table
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "channel_type": "Enum (whatsapp, instagram, tiktok, snapchat)",
    "channel_id": "String (255) - Platform-specific ID (phone, page_id)",
    "channel_name": "String (255) - Display name",
    "access_token": "Text - Encrypted OAuth token",
    "token_expires_at": "Timestamp - Nullable",
    "refresh_token": "Text - Encrypted, Nullable",
    "webhook_verified": "Boolean",
    "status": "Enum (pending, active, error, disconnected)",
    "last_sync": "Timestamp - Nullable",
    "metadata": "JSONB - Platform-specific config",
    "created_at": "Timestamp",
    "updated_at": "Timestamp"
}
```

### Conversations Table
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "channel_id": "UUID (Foreign Key to Connected Channels)",
    "session_id": "String (255) - Unique per customer-tenant pair",
    "customer_identifier": "String (255) - Phone number or social handle",
    "customer_name": "String (255) - Nullable",
    "started_at": "Timestamp",
    "last_message_at": "Timestamp",
    "status": "Enum (active, resolved, expired)",
    "message_count": "Integer - Counter for analytics",
    "metadata": "JSONB - Custom fields"
}
```

### Messages Table
```python
{
    "id": "UUID (Primary Key)",
    "conversation_id": "UUID (Foreign Key to Conversations)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "message_id": "String (255) - Platform message ID",
    "direction": "Enum (inbound, outbound)",
    "content": "Text - Message text",
    "content_type": "Enum (text, image, video, audio, document) - Phase 4",
    "sender_role": "Enum (customer, bot, human_agent) - Phase 5",
    "timestamp": "Timestamp - Platform timestamp",
    "received_at": "Timestamp - When Wafaa received it",
    "processed_at": "Timestamp - Nullable, when response sent",
    "status": "Enum (received, processing, sent, failed, delivered, read)",
    "error": "Text - Nullable, error message if failed",
    "metadata": "JSONB - RAG context, tokens used, etc."
}
```

### Webhook Events Table
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants) - Nullable initially",
    "channel_type": "Enum (whatsapp, instagram)",
    "event_type": "String (100) - message, status, account_update",
    "payload": "JSONB - Raw webhook payload",
    "signature": "String (512) - Webhook signature for verification",
    "signature_valid": "Boolean",
    "processed": "Boolean",
    "processed_at": "Timestamp - Nullable",
    "created_at": "Timestamp"
}
```

### Message Queue Jobs Table
```python
{
    "id": "UUID (Primary Key)",
    "tenant_id": "UUID (Foreign Key to Tenants)",
    "message_id": "UUID (Foreign Key to Messages)",
    "job_id": "String (255) - Celery task ID",
    "status": "Enum (queued, processing, completed, failed)",
    "retry_count": "Integer - Default 0",
    "error": "Text - Nullable",
    "created_at": "Timestamp",
    "completed_at": "Timestamp - Nullable"
}
```

## API Endpoints

### Channel Management
- `GET /api/v1/channels` - List tenant's connected channels
- `POST /api/v1/channels/whatsapp/connect` - Initiate WhatsApp OAuth
- `POST /api/v1/channels/instagram/connect` - Initiate Instagram OAuth
- `GET /api/v1/channels/{channel_id}` - Get channel details
- `DELETE /api/v1/channels/{channel_id}` - Disconnect channel
- `POST /api/v1/channels/{channel_id}/test` - Send test message

### OAuth Callbacks
- `GET /api/v1/auth/callback/whatsapp` - WhatsApp OAuth callback
- `GET /api/v1/auth/callback/instagram` - Instagram OAuth callback

### Webhooks (Public endpoints, signature-verified)
- `GET /webhooks/whatsapp` - Webhook verification (Meta requirement)
- `POST /webhooks/whatsapp` - Receive WhatsApp messages
- `GET /webhooks/instagram` - Webhook verification
- `POST /webhooks/instagram` - Receive Instagram messages

### Conversation Management
- `GET /api/v1/conversations` - List tenant's conversations
- `GET /api/v1/conversations/{conv_id}` - Get conversation details
- `GET /api/v1/conversations/{conv_id}/messages` - List messages
- `POST /api/v1/conversations/{conv_id}/messages` - Send manual message (Phase 5)
- `PATCH /api/v1/conversations/{conv_id}` - Update status (resolve, etc.)

### Analytics (Read-only for Phase 3)
- `GET /api/v1/analytics/messages/count` - Message count by date range
- `GET /api/v1/analytics/conversations/summary` - Active/resolved breakdown

## Directory Structure Updates
```
wafaa-backend/
├── app/
│   ├── models/
│   │   ├── channel.py (new)
│   │   ├── conversation.py (new)
│   │   └── message.py (new)
│   ├── schemas/
│   │   ├── channel.py (new)
│   │   ├── conversation.py (new)
│   │   └── message.py (new)
│   ├── api/v1/
│   │   ├── channels.py (new)
│   │   ├── conversations.py (new)
│   │   └── webhooks.py (new)
│   ├── services/
│   │   ├── whatsapp_service.py (new)
│   │   ├── instagram_service.py (new)
│   │   ├── message_router.py (new)
│   │   ├── session_manager.py (new)
│   │   └── response_generator.py (new)
│   ├── workers/
│   │   └── message_processor.py (new)
│   └── utils/
│       ├── encryption.py (new)
│       └── webhook_validator.py (new)
└── tests/
    ├── test_webhooks.py (new)
    ├── test_channels.py (new)
    └── test_message_flow.py (new)
```

## Message Processing Pipeline

### Step 1: Webhook Reception
```python
# POST /webhooks/whatsapp
# Headers: X-Hub-Signature-256: sha256=...

{
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {
                    "phone_number_id": "PHONE_NUMBER_ID",
                    "display_phone_number": "+1234567890"
                },
                "messages": [{
                    "from": "+9876543210",
                    "id": "wamid.XXX",
                    "timestamp": "1644444444",
                    "text": {
                        "body": "What are your hours?"
                    },
                    "type": "text"
                }]
            },
            "field": "messages"
        }]
    }]
}
```

### Step 2: Webhook Validation & Routing
```python
# 1. Verify signature
signature = request.headers["X-Hub-Signature-256"]
expected = hmac.new(META_APP_SECRET, request.body, sha256).hexdigest()
assert signature == f"sha256={expected}"

# 2. Store raw event in webhook_events table
event = WebhookEvent(
    channel_type="whatsapp",
    payload=request.json(),
    signature=signature,
    signature_valid=True
)
db.add(event)

# 3. Route to appropriate handler
phone_number = payload["entry"][0]["changes"][0]["value"]["metadata"]["display_phone_number"]
channel = db.query(ConnectedChannel).filter(
    channel_id=phone_number,
    channel_type="whatsapp"
).first()

if not channel:
    return {"status": "error", "message": "Unknown phone number"}

tenant_id = channel.tenant_id
```

### Step 3: Session Management
```python
# Create or retrieve conversation
customer_phone = message["from"]
session_id = f"{tenant_id}:{customer_phone}"

conversation = db.query(Conversation).filter(
    session_id=session_id,
    status="active"
).first()

if not conversation:
    conversation = Conversation(
        tenant_id=tenant_id,
        channel_id=channel.id,
        session_id=session_id,
        customer_identifier=customer_phone,
        started_at=datetime.utcnow()
    )
    db.add(conversation)

# Store inbound message
msg = Message(
    conversation_id=conversation.id,
    tenant_id=tenant_id,
    message_id=message["id"],
    direction="inbound",
    content=message["text"]["body"],
    content_type="text",
    sender_role="customer",
    timestamp=datetime.fromtimestamp(int(message["timestamp"])),
    status="received"
)
db.add(msg)
db.commit()

# Queue for processing
job = celery_app.send_task(
    "process_message",
    kwargs={"message_id": str(msg.id)}
)
```

### Step 4: Async Message Processing (Celery)
```python
@celery_app.task(bind=True, max_retries=3)
def process_message(self, message_id: str):
    msg = db.query(Message).get(message_id)
    tenant = db.query(Tenant).get(msg.tenant_id)
    config = db.query(TenantConfig).filter(tenant_id=msg.tenant_id).first()
    
    # Update status
    msg.status = "processing"
    db.commit()
    
    try:
        # Retrieve conversation history (last 5 messages)
        history = db.query(Message).filter(
            conversation_id=msg.conversation_id
        ).order_by(Message.timestamp.desc()).limit(5).all()
        
        # Format for context
        context_messages = [
            {"role": "customer" if m.direction == "inbound" else "assistant",
             "content": m.content}
            for m in reversed(history)
        ]
        
        # RAG query
        from app.services.rag_engine import RAGEngine
        rag = RAGEngine(tenant_id=msg.tenant_id)
        response_text = rag.generate_response(
            query=msg.content,
            config=config,
            conversation_history=context_messages
        )
        
        # Send via WhatsApp API
        from app.services.whatsapp_service import WhatsAppService
        wa_service = WhatsAppService(channel_id=msg.conversation.channel_id)
        wa_service.send_message(
            to=msg.conversation.customer_identifier,
            message=response_text
        )
        
        # Store outbound message
        outbound = Message(
            conversation_id=msg.conversation_id,
            tenant_id=msg.tenant_id,
            message_id=f"wafaa-{uuid4()}",
            direction="outbound",
            content=response_text,
            content_type="text",
            sender_role="bot",
            timestamp=datetime.utcnow(),
            status="sent"
        )
        db.add(outbound)
        
        # Update message status
        msg.status = "processed"
        msg.processed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        msg.status = "failed"
        msg.error = str(e)
        db.commit()
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
```

### Step 5: Response Delivery
```python
# WhatsApp API call
POST https://graph.facebook.com/v18.0/PHONE_NUMBER_ID/messages
Headers:
    Authorization: Bearer {ACCESS_TOKEN}
    Content-Type: application/json

Body:
{
    "messaging_product": "whatsapp",
    "to": "+9876543210",
    "type": "text",
    "text": {
        "body": "We're open Monday-Friday 9 AM to 9 PM, and weekends 10 AM to 8 PM."
    }
}

# Response
{
    "messaging_product": "whatsapp",
    "contacts": [{
        "input": "+9876543210",
        "wa_id": "9876543210"
    }],
    "messages": [{
        "id": "wamid.YYY"
    }]
}
```

## OAuth Flow Details

### WhatsApp Connection
```python
# Step 1: Initiate OAuth
GET /api/v1/channels/whatsapp/connect
→ Redirect to Meta OAuth URL with scopes:
  - whatsapp_business_messaging
  - whatsapp_business_management

# Step 2: User grants permission on Meta
# Step 3: Meta redirects to callback
GET /api/v1/auth/callback/whatsapp?code=AUTH_CODE

# Step 4: Exchange code for token
POST https://graph.facebook.com/v18.0/oauth/access_token
Body: {
    "client_id": META_APP_ID,
    "client_secret": META_APP_SECRET,
    "code": AUTH_CODE
}

Response: {
    "access_token": "long-lived-token",
    "token_type": "bearer",
    "expires_in": 5184000  # 60 days
}

# Step 5: Store encrypted token
channel = ConnectedChannel(
    tenant_id=current_user.tenant_id,
    channel_type="whatsapp",
    access_token=encrypt(access_token),
    token_expires_at=now() + timedelta(days=60)
)

# Step 6: Subscribe webhook
POST https://graph.facebook.com/v18.0/PHONE_NUMBER_ID/subscribed_apps
Headers: Authorization: Bearer {access_token}
Body: {
    "webhooks": ["messages"]
}
```

## Environment Variables (Additional)
```
# Meta/Facebook
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
META_WEBHOOK_VERIFY_TOKEN=random-token-you-choose

# WhatsApp (if using Meta Cloud API)
WHATSAPP_PHONE_NUMBER_ID=your-phone-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-id

# OR Twilio (alternative)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_WHATSAPP_NUMBER=+14155238886

# Instagram
INSTAGRAM_APP_ID=your-app-id
INSTAGRAM_APP_SECRET=your-app-secret

# Encryption (for storing OAuth tokens)
ENCRYPTION_KEY=fernet-key-generated-securely

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Message Processing
MESSAGE_PROCESS_TIMEOUT_SECONDS=30
MAX_MESSAGE_RETRIES=3
```

## Definition of Done

### Code Requirements
- [ ] WhatsApp webhook endpoint receives and validates signatures
- [ ] Instagram webhook endpoint receives and validates signatures
- [ ] OAuth flow stores access tokens encrypted in database
- [ ] Message router identifies tenant by phone number/page mapping
- [ ] Session manager creates/retrieves conversations correctly
- [ ] Celery worker processes messages asynchronously
- [ ] RAG engine called with conversation history for context
- [ ] WhatsApp API sends response successfully
- [ ] Instagram API sends response successfully
- [ ] Failed sends retry 3 times with exponential backoff
- [ ] Duplicate message detection via message_id

### Testing Requirements
- [ ] Unit test: webhook signature validation (valid and invalid)
- [ ] Unit test: tenant identification from phone number
- [ ] Integration test: receive WhatsApp message → store in DB
- [ ] Integration test: full flow (webhook → RAG → response sent)
- [ ] Test conversation history included in RAG context
- [ ] Test message ordering preserved in multi-message bursts
- [ ] Test OAuth callback stores token correctly
- [ ] Test token refresh when expired (Phase 4 enhancement)
- [ ] Test data isolation: Tenant A message doesn't trigger Tenant B response
- [ ] Load test: 50 concurrent webhooks processed successfully

### Functional Requirements
- [ ] Tenant can connect WhatsApp Business account via OAuth
- [ ] Tenant can connect Instagram Business account via OAuth
- [ ] Connected channels show "Active" status in dashboard
- [ ] Customer sends WhatsApp message, receives response within 10s
- [ ] Response content matches RAG query result
- [ ] Conversation persisted in database with all messages
- [ ] Tenant can view conversation history in UI (Phase 4 enhancement)
- [ ] Multi-turn conversation maintains context (test with 5 back-and-forth)
- [ ] Bot refuses to answer off-topic questions per config
- [ ] Webhook verification passes Meta's initial test

### Performance Requirements
- [ ] Webhook endpoint responds within 200ms (Meta timeout requirement)
- [ ] Message processing completes within 10 seconds for 95% of messages
- [ ] System handles 100 messages/minute without queuing delays
- [ ] RAG query completes within 3 seconds
- [ ] API call to Meta/Instagram completes within 2 seconds

### Security Requirements
- [ ] All webhook signatures validated before processing
- [ ] Access tokens stored encrypted (Fernet or AES-256)
- [ ] Webhook verify token kept secret (not in code)
- [ ] OAuth callback validates state parameter (CSRF protection)
- [ ] Rate limiting applied to webhook endpoints (100/min per IP)
- [ ] Customer phone numbers/IDs stored securely
- [ ] No sensitive data logged in plain text

### Documentation Requirements
- [ ] README updated with Meta app setup instructions
- [ ] Webhook URL configuration documented
- [ ] OAuth flow diagram added
- [ ] Message processing pipeline flowchart provided
- [ ] Example webhook payloads documented
- [ ] Troubleshooting guide for common connection errors
- [ ] Rate limit handling explained

## Success Metrics
- 99% of webhooks processed successfully
- 95% of responses sent within 10 seconds
- Zero unauthorized channel access attempts
- 90%+ customer satisfaction based on bot responses (Phase 5 measurement)
- <1% message delivery failures

## Known Limitations & Future Work
- **Phase 3 Limitation**: Text messages only (no images, videos, voice)
- **Phase 4**: Add media handling support
- **Phase 5**: Add human agent handoff when bot cannot answer
- **Phase 6**: Add message templates for common responses
- **Phase 7**: Add analytics dashboard for message metrics

## Next Phase Dependencies
Phase 4 (Admin Dashboard & Analytics) requires:
- Conversation and message data from this phase
- Channel connection status for display
- Message counts and timestamps for analytics charts
