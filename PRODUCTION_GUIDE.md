# Production Deployment Guide (purrfectspots.xyz)

This guide details how to deploy the Purrfect Spots application to your production server with the custom domain `purrfectspots.xyz`.

## Prerequisites

- A Virtual Private Server (VPS) (e.g., DigitalOcean, AWS, Vultr)
- Docker & Docker Compose installed
- Domain `purrfectspots.xyz` pointing to your server's IP address (A Record)

## 1. Domain Configuration (DNS)

Ensure your DNS settings are correct:

| Type | Name | Content |
| :--- | :--- | :--- |
| A | @ | `YOUR_SERVER_IP` |
| A | www | `YOUR_SERVER_IP` |

## 2. Server Setup

### Prepare Directory

Clone your repository or copy the project files to your server (e.g., `/opt/purrfect-spots`).

### Environment Configuration

1.  **Backend Environment**:
    Copy the template and fill in the secrets.
    ```bash
    cp backend/.env.production.example backend/.env
    nano backend/.env
    ```
    *   Set `JWT_SECRET` and `JWT_REFRESH_SECRET` to strong random strings.
    *   Set `GOOGLE_CLIENT_SECRET`, `AWS` keys, etc.

2.  **Frontend Environment**:
    The frontend configuration is baked into the image at build time. We configured `docker-compose.prod.yml` to use the correct values.

## 3. SSL & Reverse Proxy (Host Level)

We recommend running Nginx on the host machine to handle SSL termination and forward traffic to the Docker container.

### Install Nginx & Certbot

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### Configure Nginx

Create a new configuration file: `/etc/nginx/sites-available/purrfectspots.xyz`

```nginx
server {
    server_name purrfectspots.xyz www.purrfectspots.xyz;

    location / {
        proxy_pass http://localhost:3000; # Forward to Frontend Container
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/purrfectspots.xyz /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Enable SSL (HTTPS)

Run Certbot to automatically obtain and configure SSL certificates:

```bash
sudo certbot --nginx -d purrfectspots.xyz -d www.purrfectspots.xyz
```

Follow the prompts. Choose to redirect HTTP to HTTPS.

## 4. Deploy Application

Run the application using the production compose file:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## 5. Verification

1.  Visit `https://purrfectspots.xyz`.
2.  Check the browser console for any Content Security Policy (CSP) errors.
3.  Test login and API calls.

## Troubleshooting

- **Logs**:
    ```bash
    docker-compose -f docker-compose.prod.yml logs -f
    ```
- **Nginx Logs (Host)**:
    ```bash
    sudo tail -f /var/log/nginx/error.log
    ```
