# Echotome v3.2 Production Deployment Guide

**Version**: 3.2.0
**Edition**: Session & Locality Enforcement
**Last Updated**: 2025-11-27

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [API Server Deployment](#api-server-deployment)
4. [Session Management](#session-management)
5. [Security Configuration](#security-configuration)
6. [Monitoring & Observability](#monitoring--observability)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum**:
- Python 3.10+
- 2 GB RAM
- 10 GB disk space
- Linux/macOS/Windows

**Recommended for Production**:
- Python 3.11+
- 4+ GB RAM
- 50+ GB SSD
- Linux (Ubuntu 22.04 LTS or similar)
- Dedicated storage for session directories

### Dependencies

```bash
# Core dependencies
numpy
soundfile
Pillow
cryptography>=41.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
packaging>=23.0

# Development/Testing
pytest>=7.4.0
httpx>=0.25.0
black>=23.0.0
ruff>=0.1.0
```

---

## Installation

### Option 1: pip install (recommended)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Echotome
pip install echotome

# Verify installation
echotome --version
# Output: Echotome v3.2.0 (Session & Locality Enforcement)
```

### Option 2: From source

```bash
# Clone repository
git clone https://github.com/your-org/echotome.git
cd echotome

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Run tests
pytest tests/
```

---

## API Server Deployment

### Development Server

```bash
# Start dev server
echotome-api

# Or with uvicorn directly
uvicorn echotome.api:app --host 0.0.0.0 --port 8000 --reload
```

### Production Server (systemd)

**1. Create service user**:

```bash
sudo useradd -r -s /bin/false echotome
sudo mkdir -p /opt/echotome
sudo chown echotome:echotome /opt/echotome
```

**2. Create systemd service** (`/etc/systemd/system/echotome.service`):

```ini
[Unit]
Description=Echotome v3.2 API Server
After=network.target

[Service]
Type=simple
User=echotome
Group=echotome
WorkingDirectory=/opt/echotome
Environment="PATH=/opt/echotome/venv/bin"
ExecStart=/opt/echotome/venv/bin/uvicorn echotome.api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/echotome /home/echotome/.echotome

[Install]
WantedBy=multi-user.target
```

**3. Enable and start**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable echotome
sudo systemctl start echotome
sudo systemctl status echotome
```

### Production Server (Docker)

**Dockerfile**:

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -r -s /bin/false echotome

# Copy application
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Create session directory
RUN mkdir -p /home/echotome/.echotome/sessions && \
    chown -R echotome:echotome /home/echotome

USER echotome

EXPOSE 8000

CMD ["uvicorn", "echotome.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  echotome:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - echotome-sessions:/home/echotome/.echotome/sessions
      - echotome-vaults:/opt/echotome/vaults
    environment:
      - ECHOTOME_LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/info"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  echotome-sessions:
  echotome-vaults:
```

### Reverse Proxy (nginx)

```nginx
upstream echotome {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name echotome.example.com;

    ssl_certificate /etc/letsencrypt/live/echotome.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/echotome.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # File upload limits (for audio files)
    client_max_body_size 100M;

    location / {
        proxy_pass http://echotome;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings for long-running KDF operations
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

---

## Session Management

### v3.2 Session Architecture

**Session directories**: `~/.echotome/sessions/<session_id>/`

**Profile-Based TTLs**:
- Quick Lock: 1 hour (3600s)
- Ritual Lock: 20 minutes (1200s)
- Black Vault: 5 minutes (300s)

### Session Cleanup

**Automatic cleanup** (recommended):

```bash
# Add to crontab
*/5 * * * * /opt/echotome/venv/bin/python -c "from echotome.sessions import get_session_manager; get_session_manager().cleanup_expired_sessions()"
```

**Manual cleanup**:

```bash
# Via CLI
echotome session cleanup

# Via API
curl -X POST http://localhost:8000/sessions/cleanup
```

### Session Monitoring

```bash
# List active sessions
echotome session list

# Check session files
echotome session files <session_id>

# Emergency lock all
echotome session lock-all
```

---

## Security Configuration

### Locality Enforcement (v3.2)

**Enforced at code level** (`echotome/privacy.py`):

```python
PRIVACY_STRICT = True              # Strict privacy mode
ALLOW_THIRD_PARTY_UPLOADS = False  # No external uploads
ALLOW_EXTERNAL_TELEMETRY = False   # No telemetry
NETWORK_ISOLATED = True            # Local-only operation
```

### File System Security

**Session directory permissions**:

```bash
chmod 700 ~/.echotome/sessions
chown -R echotome:echotome ~/.echotome
```

**Secure deletion** (v3.2):

- Enabled by default for Ritual Lock and Black Vault
- 3-pass overwrite: zeros, ones, random data
- Memory zeroing before deallocation

### API Security

**HTTPS only** (production):

```bash
# Generate Let's Encrypt certificate
certbot certonly --nginx -d echotome.example.com
```

**Rate limiting** (nginx):

```nginx
limit_req_zone $binary_remote_addr zone=echotome:10m rate=10r/s;

location / {
    limit_req zone=echotome burst=20 nodelay;
    # ... proxy settings
}
```

**Authentication** (if needed):

```python
# Add to echotome/api.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/decrypt")
async def api_decrypt(token: str = Depends(security)):
    # Validate token
    pass
```

---

## Monitoring & Observability

### Logging

**Configure logging** (`echotome/privacy.py`):

```python
import logging

logger = get_logger(__name__)
logger.setLevel(logging.INFO)

# Add file handler
fh = logging.FileHandler('/var/log/echotome/api.log')
fh.setLevel(logging.INFO)
logger.addHandler(fh)
```

**Privacy-aware logging** (v3.2):

- Audio content NEVER logged
- Passphrases NEVER logged
- Filenames redacted in logs
- Keys shown as `[REDACTED]`

### Metrics Collection

**Example Prometheus metrics**:

```python
from prometheus_client import Counter, Histogram, Gauge

# Add to echotome/api.py
decrypt_requests = Counter('echotome_decrypt_total', 'Total decrypt requests')
session_count = Gauge('echotome_sessions_active', 'Active sessions')
kdf_duration = Histogram('echotome_kdf_seconds', 'KDF operation duration')
```

### Health Checks

```bash
# API health
curl http://localhost:8000/info

# Expected response
{
  "name": "Echotome",
  "version": "3.2.0",
  "edition": "Session & Locality Enforcement",
  "locality": "All cryptographic operations performed locally"
}
```

### Session Statistics

```bash
# Active session count
curl http://localhost:8000/sessions | jq '.count'

# Session details
curl http://localhost:8000/sessions/<session_id>
```

---

## Performance Tuning

### KDF Performance

**Profile selection** based on threat model:

- **Quick Lock**: Fast (2s KDF), low security
- **Ritual Lock**: Balanced (10-30s KDF), good security
- **Black Vault**: Paranoid (60s+ KDF), maximum security

**Hardware acceleration**:

- Use machines with 4+ CPU cores
- Enable parallelism in KDF (default: 4 threads)
- Consider dedicated crypto hardware for Black Vault

### API Concurrency

**Uvicorn workers**:

```bash
# 2 * CPU cores + 1 (recommended)
uvicorn echotome.api:app --workers 9  # For 4-core system
```

**Async operations**:

```python
# API already uses FastAPI async
# No additional configuration needed
```

### Session Directory Storage

**SSD recommended**:

- Faster file I/O for decrypted content
- Lower latency for session file access

**Mount options**:

```bash
# /etc/fstab
/dev/sda1 /home/echotome/.echotome ext4 noatime,nodiratime 0 2
```

---

## Troubleshooting

### Sessions Not Expiring

**Check background cleanup**:

```bash
# Test cleanup
echotome session cleanup

# Check cron
crontab -l | grep echotome
```

**Manual cleanup**:

```bash
# Remove expired sessions
python -c "from echotome.sessions import get_session_manager; print(get_session_manager().cleanup_expired_sessions())"
```

### High Memory Usage

**Symptoms**: RAM usage increases during Black Vault operations

**Solutions**:
- Black Vault uses memory-only mode (expected)
- Limit concurrent Black Vault operations
- Ensure sessions expire promptly

### Slow KDF Operations

**Symptoms**: Decrypt operations take >60 seconds

**Solutions**:
- Check CPU usage (KDF is CPU-intensive)
- Reduce profile complexity (switch from Black Vault to Ritual Lock)
- Increase parallelism (limited by CPU cores)

### Session Files Not Found

**Symptoms**: 404 error when accessing session files

**Solutions**:
- Check session hasn't expired
- Verify session directory exists: `~/.echotome/sessions/<session_id>/`
- Check file permissions

---

## Security Checklist

Before production deployment:

- [ ] HTTPS enabled with valid certificate
- [ ] Session cleanup automated (cron)
- [ ] File permissions locked down (700 for sessions)
- [ ] Reverse proxy configured (nginx/Caddy)
- [ ] Rate limiting enabled
- [ ] Log rotation configured
- [ ] Backups configured (vault metadata only, NOT sessions)
- [ ] Health checks configured
- [ ] Monitoring/alerting set up
- [ ] Locality enforcement verified (no network calls)
- [ ] Privacy-aware logging verified (no sensitive data in logs)

---

## Support & Resources

- **Documentation**: https://github.com/your-org/echotome/docs
- **Issues**: https://github.com/your-org/echotome/issues
- **Security**: security@echotome.example.com

---

**End of Deployment Guide**
