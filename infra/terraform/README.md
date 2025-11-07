# Terraform Configuration for LegendScope Backend

This directory contains Terraform configuration to provision AWS infrastructure for the LegendScope backend.

## Prerequisites

1. [Terraform](https://www.terraform.io/downloads.html) >= 1.0
2. AWS CLI configured with credentials
3. SSH key pair created in AWS

## Quick Start

### 1. Initialize Terraform

```bash
cd infra/terraform
terraform init
```

### 2. Create terraform.tfvars

```bash
cat > terraform.tfvars << EOF
aws_region       = "us-east-1"
project_name     = "legendscope"
instance_type    = "t3.micro"
key_name         = "your-ssh-key-name"
allowed_ssh_cidr = "YOUR_IP/32"  # Replace with your IP
EOF
```

### 3. Plan and Apply

```bash
# Review changes
terraform plan

# Apply configuration
terraform apply
```

### 4. Get Outputs

```bash
terraform output
```

You'll see:
- `instance_public_ip` - Use this for EC2_HOST in GitHub secrets
- `ssh_command` - Command to connect to your instance

## What Gets Created

- **EC2 Instance**: Ubuntu 22.04 with Python 3.11, Docker, and Docker Compose pre-installed
- **Security Group**: Allows SSH (22), HTTP (80), HTTPS (443), and FastAPI (8000)
- **Elastic IP**: Static public IP address
- **User Data**: Automated setup script runs on first boot

## Post-Deployment Steps

1. SSH into the instance:
   ```bash
   ssh -i ~/.ssh/your-key.pem ubuntu@<INSTANCE_IP>
   ```

2. Create environment file:
   ```bash
   sudo nano /var/www/legendscope/.env
   ```

3. Add GitHub secrets:
   - `EC2_HOST`: Instance public IP
   - `EC2_USERNAME`: `ubuntu`
   - `EC2_SSH_KEY`: Your private SSH key content

4. Push to `main` branch to trigger deployment

## Cost Estimate

- **t3.micro** (free tier eligible): ~$0.0104/hour = ~$7.50/month
- **Elastic IP** (while attached): Free
- **Storage** (20GB gp3): ~$1.60/month

**Total**: ~$9/month (free for 12 months with AWS Free Tier)

## Cleanup

```bash
terraform destroy
```

## Security Notes

⚠️ **Important**: Update `allowed_ssh_cidr` to restrict SSH access to your IP only!

For production:
- Use a bastion host or VPN
- Enable CloudWatch logs
- Add backup configuration
- Configure SSL certificates
- Use AWS Secrets Manager for sensitive data
