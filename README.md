# LegendScope Backend

Production-ready FastAPI backend scaffold positioned for deployment on AWS EC2 with a GitHub Actions powered CI/CD pipeline.

## Features

- 🚀 FastAPI app with health and sample CRUD endpoints
- 🧪 Pytest-powered async test suite with HTTPX client
- 🧰 Ruff linting & formatting configuration
- 🔐 Environment variable management via `.env` (with example provided)
- 🖥️ GitHub Actions pipeline for automated testing and EC2 deployment
- ⚙️ Systemd service template and remote deployment script for Linux hosts
- 🐳 Docker & Docker Compose configuration with multi-stage builds
- 📦 Makefile for streamlined development workflow
- 🏗️ Terraform configuration for automated AWS infrastructure provisioning
- 📚 Comprehensive deployment documentation (manual & automated)

## Getting Started

### Prerequisites

- Python 3.11+
- `git`
- Docker & Docker Compose (optional, for containerized development)
- GNU Make (optional, for convenience commands)
- Terraform (optional, for automated infrastructure provisioning)

### Quick Start with Make

```bash
# Clone repository
git clone <repo-url>
cd LegendScope-backend

# Setup everything and run tests
make all

# Run locally
make run
```

### Manual Setup

### 1. Clone and enter the repository

```bash
git clone <repo-url>
cd LegendScope-backend
```

### 2. Create and activate a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### 3. Install dependencies

```bash
pip install -r requirements-dev.txt
```

### 4. Run the FastAPI app locally

**Using Make:**
```bash
make run
```

**Or manually:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

### 5. Run the test suite and lint checks

**Using Make:**
```bash
make lint
make test
```

**Or manually:**
```bash
ruff check .
ruff format --check .
pytest
```

## Docker Development

### Run with Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Run with Docker (standalone)

```bash
# Build image
docker build -t legendscope-backend .

# Run container
docker run -d -p 8000:8000 --env-file .env legendscope-backend

# View logs
docker logs -f <container-id>
```

### Run with Nginx reverse proxy

```bash
# Start with nginx profile
docker-compose --profile with-nginx up -d
```

## Available Make Commands

```bash
make help              # Show all available commands
make venv              # Create virtual environment
make install           # Install production dependencies
make install-dev       # Install development dependencies
make clean             # Remove venv and cache files
make lint              # Run ruff linter
make format            # Format code with ruff
make test              # Run tests
make test-cov          # Run tests with coverage
make run               # Run dev server with reload
make run-prod          # Run production server
make docker-build      # Build Docker image
make docker-run        # Run Docker container
make deploy            # Deploy to EC2
```

```bash
ruff check .
ruff format --check .
pytest
```

## Configuration

Copy the example environment file and adjust values.

```bash
cp .env.example .env
```

Environment variables are prefixed with `APP_` and support multiple deployment stages:

- `APP_ENVIRONMENT`: `development`, `staging`, or `production`
- `APP_DEBUG`: enables verbose logging
- `APP_API_PREFIX`: base path for API routes (default `/api`)
- `APP_PROJECT_NAME`: display name for docs and metadata

## AWS EC2 Deployment

### Option 1: Automated with Terraform (Recommended)

**Prerequisites:**
- Terraform >= 1.0 installed
- AWS CLI configured with credentials
- SSH key pair created in AWS

**Steps:**

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region       = "us-east-1"
project_name     = "legendscope"
instance_type    = "t3.micro"
key_name         = "your-ssh-key-name"
allowed_ssh_cidr = "YOUR_IP/32"
EOF

# Review and apply
terraform plan
terraform apply

# Get outputs
terraform output
```

📖 **Full guide**: See [`infra/terraform/README.md`](infra/terraform/README.md)

### Option 2: Manual EC2 Setup

Follow the comprehensive step-by-step guide in [`infra/EC2_MANUAL_SETUP.md`](infra/EC2_MANUAL_SETUP.md) which covers:
- EC2 instance configuration
- Security group setup
- Systemd service installation
- Docker deployment options
- Nginx reverse proxy configuration
- SSL/TLS with Let's Encrypt
- Monitoring and troubleshooting

### Quick Manual Setup

```bash
# 1. Launch Ubuntu 22.04 EC2 instance with security group allowing ports 22, 80, 443, 8000

# 2. SSH into instance
ssh -i ~/.ssh/your-key.pem ubuntu@<INSTANCE_IP>

# 3. Run automated setup script
curl -sSL https://raw.githubusercontent.com/your-org/LegendScope-backend/main/scripts/ec2-setup.sh | bash

# 4. Configure environment
sudo nano /var/www/legendscope/.env

# 5. Deploy from local machine
make deploy EC2_USER=ubuntu EC2_HOST=<INSTANCE_IP>
```

### GitHub Actions Deployment

Configure these secrets in your repository (Settings → Secrets → Actions):

| Secret | Description |
| ------ | ----------- |
| `EC2_HOST` | Public hostname or IP address of the EC2 instance |
| `EC2_USERNAME` | SSH user with deployment permissions (e.g. `ubuntu`) |
| `EC2_SSH_KEY` | Private SSH key content |
| `EC2_PORT` | Custom SSH port if not 22 (optional) |

Push to `main` branch to trigger automatic deployment.

### Docker Deployment on EC2

```bash
# SSH into EC2 instance
ssh ubuntu@<INSTANCE_IP>

# Clone or receive deployment files
cd ~/deployments/legendscope

# Run with Docker Compose
docker-compose up -d

# Or build and run with Docker
docker build -t legendscope-backend .
docker run -d -p 8000:8000 --env-file /var/www/legendscope/.env --name legendscope legendscope-backend

# Check status
docker ps
curl http://localhost:8000/api/health
```

## CI/CD Pipeline Overview

The GitHub Actions workflow in `.github/workflows/ci-cd.yml` performs the following:

1. **Test job (pull requests & pushes)**
   - Installs project dependencies
   - Runs Ruff lint & format checks
   - Executes the Pytest suite
2. **Deploy job (push to `main` only)**
   - Archives application source files
   - Uploads the archive to EC2 via SCP
   - Executes `scripts/deploy.sh` remotely to update the running service

To disable automatic deployment temporarily, disable the `deploy` job or restrict branch filters.

## Project Structure

```
.
├── app/                        # Application code
│   ├── api/                    # API routes
│   ├── core/                   # Core configuration
│   ├── main.py                 # FastAPI app entry point
│   ├── schemas.py              # Pydantic models
│   └── services.py             # Business logic
├── infra/                      # Infrastructure configuration
│   ├── nginx/                  # Nginx reverse proxy config
│   ├── systemd/                # Systemd service files
│   ├── terraform/              # Terraform IaC for AWS
│   └── EC2_MANUAL_SETUP.md     # Manual EC2 setup guide
├── scripts/                    # Deployment scripts
│   ├── deploy.sh               # EC2 deployment script
│   └── ec2-setup.sh            # EC2 initial setup script
├── tests/                      # Test suite
│   ├── __init__.py
│   └── test_items.py
├── .github/                    # GitHub configuration
│   └── workflows/
│       └── ci-cd.yml           # CI/CD pipeline
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── Makefile                    # Development commands
├── .env.example                # Environment template
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

## Cost Estimate (AWS EC2)

**t3.micro instance** (free tier eligible for 12 months):
- Instance: ~$0.0104/hour = ~$7.50/month
- Storage (20GB gp3): ~$1.60/month
- Elastic IP (attached): Free
- Data transfer: First 1GB out/month free, then ~$0.09/GB

**Total**: ~$9/month (free for 12 months with AWS Free Tier)

## Next Steps & Enhancements

### Immediate Improvements
- [ ] Add database (PostgreSQL/MySQL) with SQLAlchemy
- [ ] Implement authentication & authorization (JWT)
- [ ] Add request logging and structured logging
- [ ] Configure CORS for frontend integration
- [ ] Add rate limiting middleware

### Production Hardening
- [ ] Set up CloudWatch logs and metrics
- [ ] Configure AWS Secrets Manager for credentials
- [ ] Add SSL/TLS with Let's Encrypt or ACM
- [ ] Implement health checks and monitoring
- [ ] Add backup and disaster recovery
- [ ] Configure AWS WAF for security
- [ ] Set up auto-scaling groups
- [ ] Add Redis for caching/sessions

### Development Workflow
- [ ] Add pre-commit hooks
- [ ] Implement code coverage thresholds
- [ ] Add integration tests
- [ ] Set up staging environment
- [ ] Configure branch protection rules

## Troubleshooting

### Local Development

**Import errors:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
pip install -r requirements-dev.txt
```

**Port already in use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### EC2 Deployment

**Service won't start:**
```bash
# Check service status and logs
sudo systemctl status legendscope.service
sudo journalctl -u legendscope.service -n 50
```

**Docker container issues:**
```bash
# Check container logs
docker logs legendscope

# Restart container
docker restart legendscope
```

### CI/CD Issues

**Deployment fails:**
- Verify GitHub secrets are set correctly
- Check EC2 security group allows SSH from GitHub Actions IPs
- Ensure SSH key has correct permissions (600)
- Verify deployment directory exists on EC2

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make all`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

Happy hacking! 🎯
