---
name: api-design
description: Design REST APIs, endpoints, and Web APIs. Use when user asks to design API, create endpoints, or build a web service.
---

# API Design Skill

## When to Use

- User asks to "design API", "create endpoints"
- User asks about REST, GraphQL, web services
- Building a web API from scratch

## RESTful Conventions

### HTTP Methods

| Method | Purpose | Idempotent |
|--------|---------|------------|
| GET | Retrieve | Yes |
| POST | Create | No |
| PUT | Replace | Yes |
| PATCH | Update | No |
| DELETE | Remove | Yes |

### URL Structure

```
/resources           # Collection
/resources/:id       # Specific resource
/resources/:id/sub   # Nested
```

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

## Best Practices

1. **Use nouns for resources**: `/users` not `/getUsers`
2. **Version APIs**: `/api/v1/users`
3. **Use pagination**: `?page=1&limit=20`
4. **Filter and sort**: `?status=active&sort=date`
5. **Return consistent format**
6. **Use HATEOAS** for navigation (optional)
7. **Document everything**

## Error Response Format

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Description",
    "details": {}
  }
}
```

## Authentication

| Method | Use Case |
|--------|----------|
| API Key | Server-to-server |
| JWT | User authentication |
| OAuth 2.0 | Third-party access |
| Bearer | Token-based |

## API Security Best Practices (from roadmap.sh)

### Input Validation
- Validate all input parameters (query, path, body)
- Use schema validation (Pydantic, Marshmallow)
- Sanitize user input to prevent XSS/SQL injection
- Limit payload size to prevent DoS

### Authentication & Authorization
- Never roll your own crypto
- Use HTTPS everywhere (TLS 1.2+)
- Implement rate limiting (per IP, per user)
- Use API gateways for auth enforcement
- Store secrets in env vars, never in code

### Common Vulnerabilities (OWASP API Top 10)
1. **Broken Object Level Auth** - Check permissions per resource
2. **Broken Authentication** - Strong password policy, MFA
3. **Excessive Data Exposure** - Return only needed fields
4. **Lack of Resource & Rate Limiting** - Prevent abuse
5. **Broken Function Level Auth** - Check admin vs user perms
6. **Mass Assignment** - Whitelist allowed fields
7. **Security Misconfiguration** - Disable debug in prod
8. **Injection** - Use parameterized queries
9. **Improper Assets Management** - Document all endpoints
10. **Insufficient Logging** - Log auth failures, 4xx/5xx

### OpenAPI Specification
```yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      responses:
        '200':
          description: OK
```

## GraphQL (When to Use)
- Multiple resources needed in one request
- Client needs to specify exact fields
- Rapid prototyping with evolving schema
- Avoid over-fetching/under-fetching