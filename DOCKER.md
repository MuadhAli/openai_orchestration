# Docker Deployment Guide

This guide explains how to run the ChatGPT Web UI using Docker.

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Development Mode

For development with hot reload:

```bash
# Build and start
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Production Mode

For production deployment:

```bash
# Build and start production version
docker-compose -f docker-compose.prod.yml up --build -d
```

### 4. Automated Testing

Use the provided test scripts:

**Linux/Mac:**
```bash
./docker-test.sh
```

**Windows:**
```cmd
docker-test.bat
```

## Access the Application

Once running, open your browser and navigate to:
- **Local:** http://localhost:8000
- **Network:** http://YOUR_SERVER_IP:8000

## Docker Commands

### Basic Operations

```bash
# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Rebuild and restart
docker-compose up --build
```

### Health Check

The application includes a health check endpoint:

```bash
curl http://localhost:8000/api/health
```

### Container Management

```bash
# View running containers
docker ps

# Execute commands in container
docker-compose exec chatgpt-web-ui bash

# View container logs
docker logs chatgpt_web_ui
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `PYTHONPATH` | Python path | `/app` |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |

### Port Configuration

The application runs on port 8000 by default. To change the port:

1. Update `docker-compose.yml`:
   ```yaml
   ports:
     - "YOUR_PORT:8000"
   ```

2. Restart the application:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using port 8000
   netstat -tulpn | grep 8000
   
   # Kill the process or change port in docker-compose.yml
   ```

2. **Permission denied:**
   ```bash
   # On Linux, you might need to add your user to docker group
   sudo usermod -aG docker $USER
   # Then logout and login again
   ```

3. **API key not working:**
   - Verify your `.env` file has the correct API key
   - Check the logs: `docker-compose logs`

4. **Container won't start:**
   ```bash
   # Check container status
   docker ps -a
   
   # View detailed logs
   docker-compose logs chatgpt-web-ui
   ```

### Health Check Failures

If health checks fail:

1. Check if the application is running:
   ```bash
   docker-compose ps
   ```

2. Test the health endpoint manually:
   ```bash
   curl -v http://localhost:8000/api/health
   ```

3. Check application logs:
   ```bash
   docker-compose logs -f chatgpt-web-ui
   ```

## Production Deployment

### Security Considerations

1. **Use production compose file:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Set proper environment variables:**
   - Use secrets management for API keys
   - Set appropriate log levels
   - Configure proper restart policies

3. **Network security:**
   - Use reverse proxy (nginx, traefik)
   - Enable HTTPS
   - Configure firewall rules

### Scaling

For high-traffic deployments:

1. **Multiple workers:**
   Update Dockerfile CMD:
   ```dockerfile
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   ```

2. **Load balancing:**
   Use multiple container instances with a load balancer.

3. **Resource limits:**
   Add resource constraints to docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 512M
   ```

## Monitoring

### Log Management

Logs are configured with rotation in production:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Health Monitoring

The application includes built-in health checks:
- Container health check every 30 seconds
- API health endpoint at `/api/health`
- Automatic restart on failure

## Development

### Live Reload

Development mode includes live reload:
- Code changes trigger automatic restart
- Volume mount for real-time updates
- Debug logging enabled

### Debugging

To debug the application:

1. **Access container shell:**
   ```bash
   docker-compose exec chatgpt-web-ui bash
   ```

2. **View Python logs:**
   ```bash
   docker-compose logs -f chatgpt-web-ui
   ```

3. **Test API endpoints:**
   ```bash
   # Inside container
   curl http://localhost:8000/api/health
   ```