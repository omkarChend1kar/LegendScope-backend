# EC2 Manual Setup Guide

If you prefer not to use Terraform, follow this guide to manually set up an EC2 instance for LegendScope Backend.

## Step 1: Launch EC2 Instance

1. **Sign in to AWS Console** → Navigate to EC2

2. **Launch Instance**:
   - **Name**: `legendscope-backend`
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance type**: `t3.micro` (free tier eligible)
   - **Key pair**: Create new or use existing SSH key pair
   - **Network settings**:
     - Create security group with these inbound rules:
       - SSH (22) - Your IP only
       - HTTP (80) - 0.0.0.0/0
       - HTTPS (443) - 0.0.0.0/0
       - Custom TCP (8000) - 0.0.0.0/0
   - **Storage**: 20 GB gp3

3. **Launch instance** and wait for it to be running

4. **(Optional) Allocate Elastic IP**:
   - Go to Elastic IPs → Allocate Elastic IP address
   - Associate it with your instance

## Step 2: Connect to Instance

```bash
# Replace with your key and instance IP
ssh -i ~/.ssh/your-key.pem ubuntu@<INSTANCE_PUBLIC_IP>
```

## Step 3: Run Setup Script

On the EC2 instance, download and run the setup script:

```bash
# Download setup script
curl -O https://raw.githubusercontent.com/your-org/LegendScope-backend/main/scripts/ec2-setup.sh

# Make it executable
chmod +x ec2-setup.sh

# Run setup
./ec2-setup.sh
```

Or manually run the steps:

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev rsync git curl

# Create directories
mkdir -p ~/deployments/legendscope
sudo mkdir -p /var/www/legendscope
sudo chown $USER:$USER /var/www/legendscope

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

## Step 4: Create Environment File

```bash
# Create .env file
sudo nano /var/www/legendscope/.env
```

Add the following:

```env
APP_ENVIRONMENT=production
APP_DEBUG=false
APP_API_PREFIX=/api
APP_PROJECT_NAME=LegendScope Backend
```

## Step 5: Install Systemd Service

Upload the systemd service file:

```bash
# On your local machine
scp -i ~/.ssh/your-key.pem infra/systemd/legendscope.service ubuntu@<IP>:~

# On the EC2 instance
sudo mv ~/legendscope.service /etc/systemd/system/
sudo systemctl daemon-reload
```

## Step 6: Configure GitHub Actions

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `EC2_HOST` | Your instance public IP or Elastic IP |
| `EC2_USERNAME` | `ubuntu` |
| `EC2_SSH_KEY` | Contents of your private SSH key |
| `EC2_PORT` | `22` (optional) |

## Step 7: Deploy

### Option A: Using GitHub Actions (Recommended)

Simply push to the `main` branch:

```bash
git push origin main
```

The CI/CD pipeline will automatically deploy to your EC2 instance.

### Option B: Manual Deployment

From your local machine:

```bash
# Set environment variables
export EC2_USER=ubuntu
export EC2_HOST=<YOUR_INSTANCE_IP>

# Deploy using Makefile
make deploy
```

### Option C: Docker Deployment

```bash
# On EC2 instance
cd ~/deployments/legendscope

# Using Docker Compose
docker-compose up -d

# Or using Docker directly
docker build -t legendscope-backend .
docker run -d -p 8000:8000 --env-file /var/www/legendscope/.env legendscope-backend
```

## Step 8: Verify Deployment

```bash
# Check if service is running
sudo systemctl status legendscope.service

# Or check Docker container
docker ps

# Test the API
curl http://<INSTANCE_IP>:8000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "environment": "production",
  "project": "LegendScope Backend"
}
```

## Optional: Configure Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt-get install -y nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/legendscope
```

Add:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or IP

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/legendscope /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Optional: SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com
```

## Monitoring and Logs

```bash
# View application logs (systemd)
sudo journalctl -u legendscope.service -f

# View Docker logs
docker logs -f legendscope

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Service won't start
```bash
sudo systemctl status legendscope.service
sudo journalctl -u legendscope.service --no-pager
```

### Check Python environment
```bash
cd /var/www/legendscope
source .venv/bin/activate
python --version
pip list
```

### Test manually
```bash
cd /var/www/legendscope
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Security Hardening (Production)

1. **Restrict SSH access**: Update security group to allow only your IP
2. **Disable password authentication**:
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart sshd
   ```
3. **Enable automatic security updates**:
   ```bash
   sudo apt-get install unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```
4. **Configure CloudWatch**: Set up log shipping and monitoring
5. **Use AWS Secrets Manager**: Store sensitive configuration
6. **Enable SSL/TLS**: Use Let's Encrypt or AWS Certificate Manager
