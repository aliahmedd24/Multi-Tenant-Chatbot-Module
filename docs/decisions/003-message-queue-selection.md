# ADR-003: Message Queue Selection

## Status
Accepted

## Context
The platform needs reliable async message processing for:
- Webhook ingestion from social media platforms
- Document processing (chunking, embedding)
- Message response generation
- Analytics event processing

Requirements:
- At-least-once delivery guarantee
- Message ordering per conversation
- Replay capability for failed messages
- Scalable to 10K+ messages/minute (Phase 5)

## Options Considered

### Redis Streams
- Built on existing Redis infrastructure
- Consumer groups for parallel processing
- Message acknowledgment and replay
- Sufficient for initial scale (Phase 1-4)

### Apache Kafka
- Industry standard for high-throughput streaming
- Strong ordering guarantees
- Excellent replay and retention
- Higher operational complexity

### RabbitMQ
- Mature message broker
- Good Python support (via Celery)
- Flexible routing
- Less suited for high-throughput streaming

## Decision
Use **Redis Streams** for Phase 1-4, with **Celery** as the task framework. Migrate to **Kafka** when traffic exceeds 10K messages/minute.

## Rationale
- Redis is already in the stack (caching, sessions)
- No additional infrastructure needed
- Celery provides robust task management, retries, and monitoring
- Redis Streams supports consumer groups for horizontal scaling
- Clear migration path to Kafka at scale

## Consequences
- Limited to Redis capacity for queue storage
- Message retention limited by Redis memory
- Migration to Kafka will require worker code changes
- Celery adds a layer of abstraction over Redis Streams
