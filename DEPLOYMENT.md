# Deployment Guide for 21SIXTY CONTENT GEN

This guide provides step-by-step instructions to deploy the 21SIXTY CONTENT GEN application on a DigitalOcean droplet with subdomain `contents.2160.media`.

## Prerequisites

- A DigitalOcean droplet with Ubuntu 20.04 or later
- Root or sudo access
- Domain name configured to point to the droplet (contents.2160.media)
- OpenAI API key

## Step 1: Server Setup

### Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Install Required Software

```bash
# Install Python 3.11+ and pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install nginx
sudo apt install nginx -y

# Install FFmpeg (required for yt-dlp audio extraction)
sudo apt install ffmpeg -y

# Install git (if not already installed)
sudo apt install git -y
```

## Step 2: Application Deployment

### Create Application Directory

```bash
sudo mkdir -p /opt/content-generator
sudo chown $USER:$USER /opt/content-generator
cd /opt/content-generator
```

### Clone or Copy Application Files

If using git:
```bash
git clone <your-repo-url> .
```

Or copy files manually to `/opt/content-generator`:
```
content-generator/
├── backend/
├── frontend/
├── uploads/
└── ...
```

### Create Python Virtual Environment

```bash
cd /opt/content-generator/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

**Important:** Update the `.env` file with your OpenAI API key and other values:

```bash
# Replace 'your_actual_openai_api_key_here' with your actual OpenAI API key
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
OPENAI_MODEL=gpt-4
UPLOAD_DIR=./uploads
ALLOWED_ORIGINS=https://contents.2160.media
```

**Get your OpenAI API key:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key and paste it in the `.env` file (replace `your_actual_openai_api_key_here`)

**File location:** `/opt/content-generator/backend/.env`

### Create Uploads Directory

```bash
mkdir -p /opt/content-generator/backend/uploads
chmod 755 /opt/content-generator/backend/uploads
```

## Step 3: Systemd Service Configuration

### Create Service File

```bash
sudo nano /etc/systemd/system/content-generator.service
```

Copy the contents from `systemd/content-generator.service`, replacing `/path/to/content-generator` with `/opt/content-generator`:

```ini
[Unit]
Description=21SIXTY Content Generator FastAPI Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/content-generator/backend
Environment="PATH=/opt/content-generator/backend/venv/bin"
ExecStart=/opt/content-generator/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=content-generator

[Install]
WantedBy=multi-user.target
```

### Set Permissions

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/content-generator
sudo chmod -R 755 /opt/content-generator
```

### Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable content-generator
sudo systemctl start content-generator
sudo systemctl status content-generator
```

## Step 4: Nginx Configuration

### Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/contents.2160.media
```

Copy the contents from `nginx/contents.2160.media.conf`, replacing `/path/to/content-generator` with `/opt/content-generator`:

```nginx
server {
    listen 80;
    server_name contents.2160.media;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name contents.2160.media;

    # SSL Configuration (will be updated after certbot)
    # ssl_certificate /etc/letsencrypt/live/contents.2160.media/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/contents.2160.media/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size
    client_max_body_size 500M;
    client_body_timeout 300s;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;

    # Frontend static files
    location /static/ {
        alias /opt/content-generator/frontend/;
        try_files $uri $uri/ =404;
    }

    # Serve frontend index.html for root
    location = / {
        root /opt/content-generator/frontend;
        try_files /index.html =404;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Fallback for frontend routes
    location / {
        root /opt/content-generator/frontend;
        try_files $uri $uri/ /index.html;
    }

    # Logging
    access_log /var/log/nginx/contents.2160.media.access.log;
    error_log /var/log/nginx/contents.2160.media.error.log;
}
```

For initial setup without SSL, create a temporary HTTP-only version:

```bash
sudo nano /etc/nginx/sites-available/contents.2160.media
```

Use this configuration for initial setup:

```nginx
server {
    listen 80;
    server_name contents.2160.media;

    client_max_body_size 500M;
    client_body_timeout 300s;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;

    location /static/ {
        alias /opt/content-generator/frontend/;
        try_files $uri $uri/ =404;
    }

    location = / {
        root /opt/content-generator/frontend;
        try_files /index.html =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /opt/content-generator/frontend;
        try_files $uri $uri/ /index.html;
    }

    access_log /var/log/nginx/contents.2160.media.access.log;
    error_log /var/log/nginx/contents.2160.media.error.log;
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/contents.2160.media /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 5: SSL Certificate (Let's Encrypt)

### Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Obtain SSL Certificate

```bash
sudo certbot --nginx -d contents.2160.media
```

Follow the prompts. Certbot will automatically update your nginx configuration.

### Auto-renewal

Certbot sets up auto-renewal automatically. Test it:

```bash
sudo certbot renew --dry-run
```

## Step 6: Firewall Configuration

```bash
# Allow HTTP, HTTPS, and SSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

## Step 7: File Cleanup (Optional - Cron Job)

Set up automatic cleanup of old files:

```bash
sudo crontab -e
```

Add this line to run cleanup daily at 2 AM:

```
0 2 * * * cd /opt/content-generator/backend && /opt/content-generator/backend/venv/bin/python3 -c "from utils.file_handler import FileHandler; FileHandler().cleanup_old_files()"
```

## Step 8: Verify Installation

1. Check service status:
   ```bash
   sudo systemctl status content-generator
   ```

2. Check nginx status:
   ```bash
   sudo systemctl status nginx
   ```

3. View application logs:
   ```bash
   sudo journalctl -u content-generator -f
   ```

4. Test the API:
   ```bash
   curl http://localhost:8000/api/health
   ```

5. Visit https://contents.2160.media in your browser

## Troubleshooting

### Service Won't Start

- Check logs: `sudo journalctl -u content-generator -n 50`
- Verify Python path: `which python3`
- Check environment variables: `sudo cat /opt/content-generator/backend/.env`
- Verify file permissions

### Nginx Errors

- Test configuration: `sudo nginx -t`
- Check error logs: `sudo tail -f /var/log/nginx/contents.2160.media.error.log`
- Verify backend is running: `curl http://localhost:8000/api/health`

### API Connection Issues

- Verify backend is listening: `sudo netstat -tlnp | grep 8000`
- Check firewall: `sudo ufw status`
- Test locally: `curl http://127.0.0.1:8000/api/health`

### File Permission Issues

```bash
sudo chown -R www-data:www-data /opt/content-generator
sudo chmod -R 755 /opt/content-generator
sudo chmod -R 777 /opt/content-generator/backend/uploads
```

## Maintenance

### Update Application

```bash
cd /opt/content-generator
# Pull latest changes or copy new files
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart content-generator
```

### View Logs

```bash
# Application logs
sudo journalctl -u content-generator -f

# Nginx access logs
sudo tail -f /var/log/nginx/contents.2160.media.access.log

# Nginx error logs
sudo tail -f /var/log/nginx/contents.2160.media.error.log
```

## Security Notes

1. Keep system packages updated: `sudo apt update && sudo apt upgrade`
2. Regularly review application logs
3. Monitor OpenAI API usage to prevent unexpected costs
4. Consider setting up fail2ban for additional security
5. Keep SSL certificates renewed (auto-configured by certbot)

