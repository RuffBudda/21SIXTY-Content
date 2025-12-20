# Complete Deployment Guide for 21SIXTY CONTENT GEN

This comprehensive guide provides step-by-step instructions to deploy the 21SIXTY CONTENT GEN application on a DigitalOcean droplet with subdomain `contents.2160.media`, including SSL/HTTPS setup.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Deployment](#application-deployment)
4. [Systemd Service Configuration](#systemd-service-configuration)
5. [Nginx Configuration (HTTP)](#nginx-configuration-http)
6. [SSL Certificate Setup (HTTPS)](#ssl-certificate-setup-https)
7. [Firewall Configuration](#firewall-configuration)
8. [Verification & Testing](#verification--testing)
9. [Maintenance](#maintenance)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

- A DigitalOcean droplet with Ubuntu 20.04 or later (Python 3.12.3 recommended)
- Root or sudo access
- Domain name `contents.2160.media` configured to point to the droplet
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Basic knowledge of Linux command line and nginx

## Server Setup

### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Required Software

```bash
# Check existing Python version (should be 3.12.3 or higher)
python3 --version

# Install Python venv and pip for Python 3.12
# IMPORTANT: For Python 3.12, you MUST install python3.12-venv (not just python3-venv)
sudo apt install python3.12-venv python3-pip -y

# If you have a different Python version, replace 3.12 with your version (e.g., python3.11-venv)

# Install nginx (check if already installed)
sudo apt install nginx -y

# Install FFmpeg (required for yt-dlp audio extraction)
sudo apt install ffmpeg -y

# Install git (if not already installed)
sudo apt install git -y
```

### Step 3: Check Existing Services

Before proceeding, check what services are already running to avoid conflicts:

```bash
# Check if nginx is already running and what sites are configured
sudo systemctl status nginx
sudo ls -la /etc/nginx/sites-enabled/

# Check if ports 80, 443, or 8001 (backend) are in use
sudo ss -tlnp | grep 80
sudo ss -tlnp | grep 443
sudo ss -tlnp | grep 8001

# Check existing systemd services
sudo systemctl list-units --type=service | grep -E 'nginx|python|content'

# Note: nginx will listen on ports 80/443 (alongside other services), backend FastAPI will run on port 8001
```

## Application Deployment

### Step 4: Create Application Directory

```bash
sudo mkdir -p /opt/content-generator
sudo chown $USER:$USER /opt/content-generator
cd /opt/content-generator
```

### Step 5: Clone Application Files from GitHub

```bash
git clone https://github.com/RuffBudda/21SIXTY-Content.git .
```

Or if the directory already exists:

```bash
cd /opt/content-generator
git pull origin main
```

### Step 6: Create Python Virtual Environment

```bash
cd /opt/content-generator/backend

# IMPORTANT: Install python3.12-venv package (required for creating virtual environments)
# This is separate from python3-venv and must match your Python version
sudo apt install python3.12-venv -y

# Create virtual environment using system Python (3.12.3)
python3 -m venv venv
source venv/bin/activate

# Verify Python version in virtual environment
python --version  # Should show Python 3.12.3

# Upgrade pip
pip install --upgrade pip

# Install dependencies (includes OpenAI SDK >= 1.40.0)
pip install -r requirements.txt
```

**Note:** If you get an error "ensurepip is not available", you need to install `python3.12-venv` (or `python3.X-venv` matching your Python version). The generic `python3-venv` package may not work with Python 3.12.

### Step 7: Configure Environment Variables

```bash
cd /opt/content-generator/backend
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

### Step 8: Create Uploads Directory

```bash
mkdir -p /opt/content-generator/backend/uploads
chmod 755 /opt/content-generator/backend/uploads
```

## Systemd Service Configuration

### Step 9: Create Service File

```bash
sudo nano /etc/systemd/system/content-generator.service
```

Copy and paste this configuration:

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
# Backend runs on port 8001 (nginx listens on ports 80/443 and proxies to 8001)
ExecStart=/opt/content-generator/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
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

### Step 10: Set Permissions

```bash
# Fix ownership (use www-data user that nginx runs as)
sudo chown -R www-data:www-data /opt/content-generator
sudo chmod -R 755 /opt/content-generator

# Ensure uploads directory is writable
sudo chmod -R 775 /opt/content-generator/backend/uploads
```

### Step 11: Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable content-generator
sudo systemctl start content-generator
sudo systemctl status content-generator
```

Check that the service is running without errors. If there are issues, check the logs:

```bash
sudo journalctl -u content-generator -n 50 --no-pager
```

## Nginx Configuration (HTTP)

### Step 12: Check Existing Nginx Configuration

Before creating the new configuration, check existing nginx sites to avoid conflicts:

```bash
# List all enabled sites
sudo ls -la /etc/nginx/sites-enabled/

# Check if contents.2160.media already exists
sudo ls -la /etc/nginx/sites-available/ | grep contents

# View existing default configuration (if any)
sudo cat /etc/nginx/sites-available/default 2>/dev/null || echo "No default config"
```

If you need to disable the default nginx site:

```bash
sudo rm /etc/nginx/sites-enabled/default
```

### Step 13: Create Nginx Configuration (HTTP on Port 80)

```bash
sudo nano /etc/nginx/sites-available/contents.2160.media
```

Use this configuration (HTTP on port 80, will work alongside your scraper service):

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
        proxy_pass http://127.0.0.1:8001;
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

**Important:** At this stage, the configuration should only have HTTP (port 80). Do NOT add SSL certificate paths yet - Certbot will add them automatically.

### Step 14: Enable Site and Test

```bash
sudo ln -s /etc/nginx/sites-available/contents.2160.media /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Access the site:** `http://contents.2160.media` (port 80)

**Note:** 
- Nginx listens on port 80 for HTTP (alongside your scraper service)
- Backend FastAPI runs on port 8001 (internal only, proxied by nginx)
- Next step: Set up SSL/HTTPS for secure connections

## SSL Certificate Setup (HTTPS)

### Step 15: Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Step 16: Verify Port 80 is Accessible

Verify nginx is listening on port 80 (should already be configured):

```bash
sudo ss -tlnp | grep 80
```

If nginx is running and listening on port 80, you're good to go.

### Step 17: Check Current Nginx Configuration

**CRITICAL:** Before running certbot, ensure your nginx configuration does NOT have SSL certificate paths that don't exist:

```bash
sudo cat /etc/nginx/sites-available/contents.2160.media | grep ssl_certificate
```

If you see lines like `ssl_certificate /etc/letsencrypt/live/contents.2160.media/fullchain.pem;`, you need to remove them first.

**Important:** Your nginx config should only have a simple HTTP server block on port 80 (no SSL configuration yet). If there are SSL certificate references, remove them:

```bash
sudo nano /etc/nginx/sites-available/contents.2160.media
```

The config should look like the HTTP-only configuration from Step 13 (no `ssl_certificate` or `listen 443` lines).

After editing, test and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 18: Obtain SSL Certificate

Run certbot with the nginx plugin:

```bash
sudo certbot --nginx -d contents.2160.media
```

Follow the prompts:
- Enter your email address (for renewal reminders)
- Agree to the terms of service
- Choose whether to redirect HTTP to HTTPS (recommended: **Yes**)

Certbot will automatically:
- Obtain the SSL certificate from Let's Encrypt
- Add the HTTPS server block on port 443
- Configure SSL certificate paths
- Set up automatic HTTP to HTTPS redirect
- Preserve your existing location blocks

### Step 19: Verify SSL Configuration

After certbot completes, check your nginx configuration:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Your nginx configuration for `contents.2160.media` will now have both HTTP and HTTPS server blocks:

```nginx
# HTTP server block (redirects to HTTPS)
server {
    listen 80;
    server_name contents.2160.media;
    return 301 https://$server_name$request_uri;
}

# HTTPS server block
server {
    listen 443 ssl http2;
    server_name contents.2160.media;

    ssl_certificate /etc/letsencrypt/live/contents.2160.media/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/contents.2160.media/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

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
        proxy_pass http://127.0.0.1:8001;
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

### Step 20: Test SSL Certificate

1. Visit your site: `https://contents.2160.media`
2. Verify HTTP redirects to HTTPS: `http://contents.2160.media` should automatically redirect to `https://contents.2160.media`
3. Verify SSL certificate is valid (green padlock in browser)
4. Test that the site loads correctly over HTTPS

### Step 21: Test Certificate Auto-renewal

Certbot sets up automatic renewal automatically. Test it:

```bash
sudo certbot renew --dry-run
```

If the dry-run succeeds, your certificates will automatically renew before they expire (about 30 days before expiry).

### Important SSL Notes

1. **Ports**: 
   - HTTP: Port 80 (automatically redirects to HTTPS)
   - HTTPS: Port 443
   - Both services (scraper and contents) can use the same ports via different `server_name` directives in nginx

2. **Backend Port**: The backend FastAPI service continues to run on port 8001 (internal only, proxied by nginx)

3. **Certificate Expiry**: Let's Encrypt certificates expire after 90 days, but auto-renewal is configured to renew them automatically

4. **Multiple Services**: Your nginx can handle multiple services on ports 80/443 by using different `server_name` values. Each service gets its own server blocks.

5. **Multiple Domains**: If you need SSL for multiple domains, add them to the certbot command:
   ```bash
   sudo certbot --nginx -d contents.2160.media -d www.contents.2160.media
   ```

## Firewall Configuration

### Step 22: Configure Firewall

```bash
# Allow HTTP (port 80), HTTPS (port 443), and SSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

**Note:** Port 8001 (backend) should NOT be exposed to the internet - it's only accessible via localhost from nginx.

## Verification & Testing

### Step 23: Verify Installation

1. **Check service status:**
   ```bash
   sudo systemctl status content-generator
   ```

2. **Check nginx status:**
   ```bash
   sudo systemctl status nginx
   ```

3. **View application logs:**
   ```bash
   sudo journalctl -u content-generator -f
   ```

4. **Test the API (access via nginx):**
   ```bash
   curl http://localhost/api/health
   ```
   
   Or test backend directly on port 8001:
   ```bash
   curl http://localhost:8001/api/health
   ```

5. **Visit the site in your browser:**
   - **With SSL (HTTPS):** `https://contents.2160.media`
   - **HTTP redirect:** `http://contents.2160.media` should redirect to HTTPS

6. **Check certificate status:**
   ```bash
   sudo certbot certificates
   ```

## Maintenance

### Update Application

```bash
cd /opt/content-generator
# Pull latest changes
git pull origin main

cd backend
source venv/bin/activate
# Update dependencies if requirements.txt changed
pip install -r requirements.txt --upgrade
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

# Certbot/SSL renewal logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Check Certificate Renewal Status

```bash
# View certificate expiration dates
sudo certbot certificates

# Manually test renewal (dry-run)
sudo certbot renew --dry-run
```

## Troubleshooting

### Service Won't Start

**Symptoms:** `sudo systemctl status content-generator` shows failed status

**Solutions:**
- Check logs: `sudo journalctl -u content-generator -n 50`
- Verify Python path: `which python3`
- Check environment variables: `sudo cat /opt/content-generator/backend/.env`
- Verify file permissions: `sudo chown -R www-data:www-data /opt/content-generator`
- **If venv creation failed with "ensurepip is not available"**: Install `python3.12-venv`: `sudo apt install python3.12-venv -y`
- Check OpenAI API key is valid and correctly set in `.env` file
- Verify OpenAI SDK version: `pip show openai` (should be >= 1.40.0)

### Nginx Errors

**Symptoms:** Nginx fails to start or serve content

**Solutions:**
- Test configuration: `sudo nginx -t`
- Check error logs: `sudo tail -f /var/log/nginx/contents.2160.media.error.log`
- Verify backend is running: `curl http://localhost:8001/api/health`
- Verify nginx proxy: `curl http://localhost/api/health`
- Check nginx is listening: `sudo ss -tlnp | grep 80`

### API Connection Issues

**Symptoms:** Frontend cannot connect to backend API

**Solutions:**
- Verify backend is listening: `sudo ss -tlnp | grep 8001`
- Verify nginx is listening: `sudo ss -tlnp | grep 80`
- Check firewall: `sudo ufw status`
- Test backend locally: `curl http://127.0.0.1:8001/api/health`
- Test via nginx: `curl http://127.0.0.1/api/health`
- Check CORS settings in `.env` file

### File Permission Issues

**Symptoms:** Cannot write uploads or access files

**Solutions:**
```bash
sudo chown -R www-data:www-data /opt/content-generator
sudo chmod -R 755 /opt/content-generator
sudo chmod -R 775 /opt/content-generator/backend/uploads
```

### SSL/Certbot Issues

#### Certbot fails with "cannot load certificate" error

**Cause:** Nginx config already references SSL certificates that don't exist yet.

**Solution:**
1. Edit your nginx config: `sudo nano /etc/nginx/sites-available/contents.2160.media`
2. Remove any lines containing `ssl_certificate` or `ssl_certificate_key`
3. Remove any `listen 443` server blocks
4. Keep only the HTTP server block (port 80)
5. Test and reload: `sudo nginx -t && sudo systemctl reload nginx`
6. Run certbot again: `sudo certbot --nginx -d contents.2160.media`

#### Certbot fails with "Connection refused"

**Solutions:**
- Ensure port 80 is accessible: `sudo ss -tlnp | grep 80`
- Verify nginx is running: `sudo systemctl status nginx`
- Check that nginx has a server block listening on port 80 for the domain
- Test nginx config: `sudo nginx -t`
- Check firewall: `sudo ufw status`

#### Certificate renewal fails

**Solutions:**
- Check certbot logs: `sudo tail -f /var/log/letsencrypt/letsencrypt.log`
- Test renewal manually: `sudo certbot renew --dry-run`
- Verify DNS still points to your server: `dig contents.2160.media`
- Ensure nginx is running and accessible

#### Mixed content warnings

**Solutions:**
- Ensure all frontend resources (CSS, JS, images) are loaded over HTTPS
- Check that API calls use HTTPS endpoints
- Verify `X-Forwarded-Proto` header is set correctly in nginx config

#### SSL certificate shows as invalid

**Solutions:**
- Check certificate expiration: `sudo certbot certificates`
- Verify domain DNS is correct: `dig contents.2160.media`
- Check nginx error logs: `sudo tail -f /var/log/nginx/contents.2160.media.error.log`
- Verify certificate paths in nginx config are correct

#### Nginx configuration errors after certbot

**Solutions:**
- Check nginx syntax: `sudo nginx -t`
- Review the certbot-modified config: `sudo cat /etc/nginx/sites-available/contents.2160.media`
- Certbot should preserve your location blocks, but verify they're intact

### OpenAI API Issues

**Symptoms:** Content generation fails or API errors occur

**Solutions:**
- Verify API key is correct: Check `/opt/content-generator/backend/.env`
- Check API key is valid: Visit https://platform.openai.com/api-keys
- Verify OpenAI SDK version: `pip show openai` (should be >= 1.40.0)
- Check API usage limits: Visit https://platform.openai.com/usage
- Review application logs: `sudo journalctl -u content-generator -n 100`
- Test API key manually: Use OpenAI's API testing tools

### Revoking a Certificate

If you need to revoke a certificate (e.g., if the private key is compromised):

```bash
sudo certbot revoke --cert-path /etc/letsencrypt/live/contents.2160.media/cert.pem
```

## Security Notes

1. **Keep system packages updated:** `sudo apt update && sudo apt upgrade`
2. **Regularly review application logs**
3. **Monitor OpenAI API usage** to prevent unexpected costs: https://platform.openai.com/usage
4. **Consider setting up fail2ban** for additional security
5. **Keep SSL certificates renewed** (auto-configured by certbot)
6. **Never expose port 8001** (backend) to the internet - only accessible via nginx on localhost
7. **Use strong OpenAI API keys** and rotate them periodically
8. **Keep your `.env` file secure** - never commit it to git

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [OpenAI Usage Dashboard](https://platform.openai.com/usage)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
