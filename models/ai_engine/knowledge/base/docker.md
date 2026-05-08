# Docker (from roadmap.sh)

Source: https://roadmap.sh/docker

## What is Docker?
Docker is a platform for developing, shipping, and running applications in containers - lightweight, standalone, executable packages that include everything needed to run.

## Core Concepts

### Images vs Containers
| Concept | Description |
|---------|-------------|
| **Image** | Read-only template (like a class) |
| **Container** | Running instance of an image (like an object) |
| **Dockerfile** | Script to build images |
| **Registry** | Storage for images (Docker Hub) |

### Basic Commands
```bash
docker build -t myapp .          # Build image from Dockerfile
docker run -p 8080:80 myapp     # Run container (port mapping)
docker ps                          # List running containers
docker ps -a                       # List all containers
docker stop <container_id>         # Stop container
docker rm <container_id>           # Remove container
docker rmi <image_id>              # Remove image
docker logs <container_id>         # View logs
```

## Dockerfile Essentials

### Multi-Stage Build (Best Practice)
```dockerfile
# Build stage
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["python", "main.py"]
```

### Common Instructions
| Instruction | Purpose |
|-------------|----------|
| `FROM` | Base image |
| `WORKDIR` | Set working directory |
| `COPY` | Copy files into container |
| `RUN` | Execute commands during build |
| `EXPOSE` | Document port |
| `ENV` | Set environment variables |
| `CMD` | Default command to run |
| `ENTRYPOINT` | Fixed command (harder to override) |

## Docker Compose
Define multi-container apps in YAML.

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    environment:
      - FLASK_ENV=development
  redis:
    image: redis:alpine
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
```

Run: `docker-compose up -d`

## Best Practices
- **Use .dockerignore**: Exclude unnecessary files
- **Multi-stage builds**: Reduce image size
- **One process per container**: Follow Unix philosophy
- **Use specific tags**: Not `latest` (e.g., `python:3.11-slim`)
- **Non-root user**: Don't run as root in containers
- **Health checks**: Add `HEALTHCHECK` instruction
- **Minimize layers**: Combine RUN commands with `&&`

## Common Use Cases
- **Development environments**: Reproducible setups
- **Microservices**: Each service in its own container
- **CI/CD**: Consistent build environments
- **Local databases**: Run Postgres, Redis without installing
