# System Design Roadmap (2026)

Source: https://roadmap.sh/system-design

## Core Components

### Programming Language Choice
- Python: Fast development, AI/ML ecosystem
- Java: Enterprise, Android
- Go: Cloud-native, microservices
- Rust: Performance-critical, safety

### Databases
| Type | Examples | Use Case |
|------|---------|----------|
| Relational | PostgreSQL, MySQL | ACID, complex queries |
| NoSQL Document | MongoDB, CouchDB | Flexible schema |
| Key-Value | Redis, DynamoDB | Caching, sessions |
| Columnar | Cassandra | Analytics, time-series |
| Graph | Neo4j | Relationships |
| Search | Elasticsearch | Full-text search |

### Infrastructure
- **CDN** (Content Delivery Network): CloudFlare, CloudFront
- **Load Balancers**: Nginx, HAProxy, cloud LB
- **Caches**: Redis, Memcached
- **Proxies**: Forward, reverse proxies
- **Queues**: RabbitMQ, Kafka, SQS
- **Web Servers**: Nginx, Apache
- **Search Engines**: Elasticsearch, Solr

### Scalability Techniques
| Technique | When to Use |
|-----------|-------------|
| **Vertical Scaling** | Scale up (more CPU/RAM) |
| **Horizontal Scaling** | Add more servers |
| **Read Replicas** | High read load |
| **Sharding** | Large datasets |
| **Caching** | Repeated queries |
| **CDN** | Static assets |
| **Async/Queues** | Heavy processing |

### Architectural Patterns
- **Layered Architecture**: UI → Business → Data
- **Microservices**: Independent deployable services
- **Event-Driven**: Producer → Event Bus → Consumers
- **Serverless**: Functions as a Service (FaaS)
- **Monolith**: Single deployable unit (start here)

### Logging and Monitoring
- **Logs**: Structured logging (JSON)
- **Metrics**: Prometheus, StatsD
- **Tracing**: OpenTelemetry, Jaeger
- **Alerting**: PagerDuty, CloudWatch Alerts

## Design Considerations
- **Consistency**: Strong vs eventual consistency
- **Availability**: Uptime requirements
- **Partition Tolerance**: Network failures (CAP theorem)
- **Latency**: Response time requirements
- **Throughput**: Requests per second
- **Failure Tolerance**: Graceful degradation

## Security
- **Authentication**: JWT, OAuth 2.0, API keys
- **Authorization**: RBAC, ABAC
- **Encryption**: TLS in transit, at rest
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Prevent injection
