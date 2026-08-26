# Run Community Kenya VPS Deployment

This guide matches the current VPS shape:

- Ubuntu 26.04
- Cloudflare Tunnel via `/etc/cloudflared/config.yml`
- Existing app on `pos.sasalink.co.ke` -> `http://127.0.0.1:8000`
- Nginx installed
- Apps live under `/home/alec/apps`

Target setup:

```text
https://runcommunity.co.ke          React frontend
https://runcommunity.co.ke/api/...  Flask backend
```

## 1. Clone App

```bash
cd /home/alec/apps
git clone https://github.com/Alex-pu/walk.git runcommunity
```

## 2. Backend Setup

```bash
cd /home/alec/apps/runcommunity/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
cp .env.example .env
nano .env
```

Use production values:

```env
FLASK_ENV=production
SECRET_KEY=change-this
JWT_SECRET_KEY=change-this-too
DATABASE_URL=your-neon-postgres-url
FRONTEND_ORIGIN=https://runcommunity.co.ke,https://www.runcommunity.co.ke
APP_PUBLIC_URL=https://runcommunity.co.ke
UPLOAD_FOLDER=/home/alec/apps/runcommunity/uploads
MAIL_SERVER=rs3.rcnoc.com
MAIL_PORT=465
MAIL_USE_TLS=false
MAIL_USE_SSL=true
MAIL_USERNAME=no-reply.runcommunitykenya@sasalink.co.ke
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=no-reply.runcommunitykenya@sasalink.co.ke
```

Create uploads folder:

```bash
mkdir -p /home/alec/apps/runcommunity/uploads
chmod 700 /home/alec/apps/runcommunity/uploads
```

Run migrations:

```bash
cd /home/alec/apps/runcommunity/backend
source venv/bin/activate
flask --app run.py db upgrade
```

## 3. Systemd Service

Create:

```bash
sudo nano /etc/systemd/system/runcommunity.service
```

Paste:

```ini
[Unit]
Description=Run Community Kenya Flask backend
After=network.target

[Service]
User=alec
Group=www-data
WorkingDirectory=/home/alec/apps/runcommunity/backend
Environment="PATH=/home/alec/apps/runcommunity/backend/venv/bin"
ExecStart=/home/alec/apps/runcommunity/backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8010 run:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now runcommunity
sudo systemctl status runcommunity --no-pager
```

Backend health check:

```bash
curl http://127.0.0.1:8010/api/health
```

Expected:

```json
{"status":"ok"}
```

## 4. Frontend Build

```bash
cd /home/alec/apps/runcommunity/frontend
npm install
npm run build
```

## 5. Nginx Site

Create:

```bash
sudo nano /etc/nginx/sites-available/runcommunity
```

Paste:

```nginx
server {
    listen 127.0.0.1:8081;
    server_name runcommunity.co.ke www.runcommunity.co.ke;

    root /home/alec/apps/runcommunity/frontend/dist;
    index index.html;

    client_max_body_size 8m;

    location /api/ {
        proxy_pass http://127.0.0.1:8010/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/runcommunity /etc/nginx/sites-enabled/runcommunity
sudo nginx -t
sudo systemctl reload nginx
```

Local nginx check:

```bash
curl http://127.0.0.1:8081/api/health
```

## 6. Cloudflare Tunnel

Edit:

```bash
sudo nano /etc/cloudflared/config.yml
```

Keep the existing `pos.sasalink.co.ke` rule and add Run Community before the final 404:

```yaml
tunnel: eca11ed9-aa2d-4750-8e48-7b184f948d65
credentials-file: /home/alec/.cloudflared/eca11ed9-aa2d-4750-8e48-7b184f948d65.json

ingress:
  - hostname: pos.sasalink.co.ke
    service: http://127.0.0.1:8000

  - hostname: runcommunity.co.ke
    service: http://127.0.0.1:8081

  - hostname: www.runcommunity.co.ke
    service: http://127.0.0.1:8081

  - service: http_status:404
```

Restart:

```bash
sudo systemctl restart cloudflared
sudo systemctl status cloudflared --no-pager
```

## 7. Cloudflare DNS

`runcommunity.co.ke` must be in Cloudflare DNS.

Add DNS records:

```text
Type: CNAME
Name: @
Target: eca11ed9-aa2d-4750-8e48-7b184f948d65.cfargotunnel.com
Proxy: On

Type: CNAME
Name: www
Target: eca11ed9-aa2d-4750-8e48-7b184f948d65.cfargotunnel.com
Proxy: On
```

Some Cloudflare accounts create these automatically with:

```bash
cloudflared tunnel route dns eca11ed9-aa2d-4750-8e48-7b184f948d65 runcommunity.co.ke
cloudflared tunnel route dns eca11ed9-aa2d-4750-8e48-7b184f948d65 www.runcommunity.co.ke
```

## 8. Update Deployment Later

```bash
cd /home/alec/apps/runcommunity
git pull

cd backend
source venv/bin/activate
pip install -r requirements.txt
flask --app run.py db upgrade
sudo systemctl restart runcommunity

cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

## Notes

- The existing `pos.sasalink.co.ke` app remains on `127.0.0.1:8000`.
- Run Community backend uses `127.0.0.1:8010`.
- Nginx serves Run Community on `127.0.0.1:8081`.
- Cloudflare Tunnel exposes only the hostname routes. No public VPS ports are required.
