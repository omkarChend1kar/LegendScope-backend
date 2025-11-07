#!/usr/bin/env bash
# EC2 Initial Setup Script for Ubuntu 22.04 / Amazon Linux 2023
# Run this script on a fresh EC2 instance to prepare it for deployment

set -euo pipefail

echo "=========================================="
echo "LegendScope Backend - EC2 Setup Script"
echo "=========================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS. Exiting."
    exit 1
fi

echo "Detected OS: $OS"

# Update system packages
echo "Updating system packages..."
if [ "$OS" = "ubuntu" ]; then
    sudo apt-get update
    sudo apt-get upgrade -y
elif [ "$OS" = "amzn" ]; then
    sudo yum update -y
fi

# Install Python 3.11
echo "Installing Python 3.11..."
if [ "$OS" = "ubuntu" ]; then
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
elif [ "$OS" = "amzn" ]; then
    sudo yum install -y python3.11 python3.11-pip
fi

# Install additional dependencies
echo "Installing additional dependencies..."
if [ "$OS" = "ubuntu" ]; then
    sudo apt-get install -y rsync git curl nginx
elif [ "$OS" = "amzn" ]; then
    sudo yum install -y rsync git curl nginx
fi

# Create deployment directories
echo "Creating deployment directories..."
mkdir -p ~/deployments/legendscope
sudo mkdir -p /var/www/legendscope
sudo chown "$USER":"$USER" /var/www/legendscope

# Install Docker (optional but recommended)
echo "Installing Docker..."
if [ "$OS" = "ubuntu" ]; then
    # Install Docker on Ubuntu
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker "$USER"
    rm get-docker.sh
elif [ "$OS" = "amzn" ]; then
    # Install Docker on Amazon Linux
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker "$USER"
fi

# Install Docker Compose
echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure firewall
echo "Configuring firewall..."
if [ "$OS" = "ubuntu" ]; then
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp
    echo "y" | sudo ufw enable || true
elif [ "$OS" = "amzn" ]; then
    sudo firewall-cmd --permanent --add-service=ssh
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --reload || true
fi

# Create .env file template
echo "Creating .env template..."
cat > /var/www/legendscope/.env.template << 'EOF'
APP_ENVIRONMENT=production
APP_DEBUG=false
APP_API_PREFIX=/api
APP_PROJECT_NAME=LegendScope Backend
EOF

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy your .env.template to .env and configure:"
echo "   cd /var/www/legendscope && cp .env.template .env && nano .env"
echo ""
echo "2. Add GitHub deployment secrets in your repository:"
echo "   - EC2_HOST: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "   - EC2_USERNAME: $USER"
echo "   - EC2_SSH_KEY: (your private SSH key)"
echo ""
echo "3. Log out and back in for Docker group changes to take effect:"
echo "   exit"
echo ""
echo "4. Deploy using GitHub Actions or manually:"
echo "   - GitHub Actions: Push to main branch"
echo "   - Manual: make deploy EC2_USER=$USER EC2_HOST=<your-ec2-ip>"
echo ""
