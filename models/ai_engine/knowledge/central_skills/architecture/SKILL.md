---
name: architecture
description: System design, architecture patterns, and scalability. Use when user asks about architecture, system design, or scalability.
---

# Architecture Skill

## When to Use

- User asks about "system design"
- User asks about "architecture"
- Planning a new system
- Scaling considerations

## Common Patterns

### Layered Architecture
```
┌─────────────┐
│   UI Layer  │
├─────────────┤
│  Business   │
│    Layer    │
├─────────────┤
│    Data     │
│    Layer    │
└─────────────┘
```

### Microservices
- Independent deployable services
- Own database per service
- API communication
- Scales independently

### Event-Driven
```
Producer → Event Bus → Consumers
```
- Decoupled components
- Scalable
- Fault tolerant

## Scalability Principles

| Technique | Use When |
|-----------|----------|
| Read replicas | High read load |
| Caching | Repeated queries |
| Queue/async | Heavy processing |
| CDN | Static assets |
| Sharding | Large datasets |

## Decision Factors

1. **Team size**: Small team = fewer services
2. **Traffic**: High traffic = more caching/queues
3. **Latency**: Low latency = more compute
4. **Complexity**: Time to market Matters

## System Design Roadmap Patterns

### Scalability Patterns
| Pattern | When to Use | Benefit |
|---------|-------------|---------|
| **Load Balancer** | Multiple servers | Distribute traffic |
| **Read Replicas** | High read load | Offload DB reads |
| **Caching (Redis)** | Repeated queries | Sub-ms response |
| **CDN** | Static assets | Global edge delivery |
| **Sharding** | Large datasets | Horizontal DB scale |
| **Queue (RabbitMQ)** | Async processing | Decouple components |
| **Service Mesh** | Microservices | Traffic management |

### Database Choices
| Database | Use Case |
|----------|----------|
| PostgreSQL | Relational, ACID, complex queries |
| MongoDB | Document store, flexible schema |
| Redis | Caching, sessions, real-time |
| Elasticsearch | Full-text search, logging |

### High-Level Design Checklist
- [ ] Define API contracts (REST/GraphQL)
- [ ] Identify data models and relationships
- [ ] Choose database (SQL vs NoSQL)
- [ ] Plan caching strategy
- [ ] Consider async processing (queues)
- [ ] Design for failure (circuit breakers)
- [ ] Monitor (logs, metrics, traces)

## Design Questions to Ask

- What are the read/write ratios?
- What are the latency requirements?
- How will it scale?
- What's the failure tolerance?
- What's the data growth rate?