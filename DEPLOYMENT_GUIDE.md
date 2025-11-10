# Azure DevOps CI/CD Setup Guide

## Prerequisites Checklist
- ✅ Azure DevOps Organization created
- ✅ Azure Container Registry (ACR) created
- ✅ Azure VM created and running

## Step-by-Step Setup

### 1. Prepare Your Azure VM

SSH into your VM and run these commands:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin -y

# Create app directory
mkdir -p /home/azureuser/app
cd /home/azureuser/app

# Create .env file (copy from .env.production.example)
nano .env
# Paste your actual values and save (Ctrl+X, Y, Enter)

# Copy docker-compose.prod.yml to the VM
nano docker-compose.prod.yml
# Paste the content and save
```

### 2. Get Your ACR Credentials

In Azure Portal:
1. Go to your Container Registry
2. Click "Access keys" in the left menu
3. Enable "Admin user"
4. Copy:
   - Login server (e.g., myregistry.azurecr.io)
   - Username
   - Password

### 3. Setup Azure DevOps Project

1. Go to https://dev.azure.com
2. Create a new project (or use existing)
3. Go to "Repos" → "Files"
4. Import or push your code repository

### 4. Create Service Connections

#### A. ACR Service Connection
1. In Azure DevOps, go to Project Settings (bottom left)
2. Click "Service connections"
3. Click "New service connection"
4. Select "Docker Registry"
5. Choose "Azure Container Registry"
6. Select your subscription and ACR
7. Name it: **ACR-ServiceConnection**
8. Click "Save"

#### B. SSH Service Connection
1. In Service connections, click "New service connection"
2. Select "SSH"
3. Fill in:
   - Host name: Your VM's public IP
   - Port: 22
   - Username: azureuser (or your VM username)
   - Private key: Paste your SSH private key
4. Name it: **VM-SSH-ServiceConnection**
5. Click "Save"

### 5. Create Pipeline Variables (Secrets)

1. Go to "Pipelines" → "Library"
2. Click "+ Variable group"
3. Name it: "Production-Secrets"
4. Add these variables (click the lock icon to make them secret):
   - `ACR_USERNAME`: Your ACR username
   - `ACR_PASSWORD`: Your ACR password
   - `MYSQL_ROOT_PASSWORD`: Your MySQL root password
   - `MYSQL_PASSWORD`: Your MySQL user password
   - `OPENAI_API_KEY`: Your OpenAI API key

### 6. Update azure-pipelines.yml

Edit the `azure-pipelines.yml` file and replace:
- `your-acr-name` with your actual ACR name (e.g., myappregistry)

### 7. Create the Pipeline

1. Go to "Pipelines" → "Pipelines"
2. Click "New pipeline"
3. Select "Azure Repos Git" (or GitHub if your code is there)
4. Select your repository
5. Choose "Existing Azure Pipelines YAML file"
6. Select `/azure-pipelines.yml`
7. Click "Continue"
8. Click "Run"

### 8. Configure VM Firewall

Make sure your VM allows traffic on port 8000:

```bash
# On your VM
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

In Azure Portal:
1. Go to your VM → "Networking"
2. Add inbound port rule for port 8000

## Testing the Pipeline

1. Make a small change to your code
2. Commit and push to main branch
3. Pipeline will automatically trigger
4. Watch the pipeline run in Azure DevOps
5. Once complete, access your app at: http://YOUR_VM_IP:8000

## Troubleshooting

### Pipeline fails at Docker login
- Check ACR service connection credentials
- Verify ACR admin user is enabled

### Pipeline fails at SSH step
- Verify SSH service connection
- Check VM firewall allows SSH (port 22)
- Ensure SSH key is correct

### App doesn't start on VM
- SSH to VM and check logs: `sudo docker compose logs -f`
- Verify .env file exists with correct values
- Check if ports are available: `sudo netstat -tulpn | grep 8000`

### Can't access app from browser
- Check VM firewall rules
- Verify Azure Network Security Group allows port 8000
- Check if containers are running: `sudo docker ps`

## Useful Commands on VM

```bash
# View running containers
sudo docker ps

# View logs
sudo docker compose logs -f

# Restart containers
sudo docker compose restart

# Stop containers
sudo docker compose down

# View images
sudo docker images

# Clean up old images
sudo docker image prune -f
```

## Next Steps

- Set up custom domain name
- Configure HTTPS with Let's Encrypt
- Set up monitoring and alerts
- Configure auto-scaling (optional)
