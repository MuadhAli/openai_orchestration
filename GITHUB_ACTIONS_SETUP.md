# GitHub Actions CI/CD Setup Guide

Much simpler than Azure DevOps! GitHub Actions has FREE runners (2000 minutes/month).

## Setup Steps

### 1. Push Your Code to GitHub

If you don't have a GitHub repo yet:

```bash
# Create a new repo on GitHub first, then:
wsl git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
wsl git branch -M main
wsl git push -u origin main
```

If you already have a GitHub repo:
```bash
wsl git add .
wsl git commit -m "Add GitHub Actions CI/CD"
wsl git push origin main
```

### 2. Get Your ACR Credentials

In Azure Portal:
1. Go to your Container Registry (orchestrationAgent)
2. Click **Access keys**
3. Enable **Admin user**
4. Copy:
   - Username
   - Password

### 3. Get Your VM SSH Key

You should have the SSH private key you used when creating the VM. If not:
- On your local machine, find it (usually `~/.ssh/id_rsa` or the key you downloaded from Azure)
- Copy the entire content of the private key file

### 4. Add Secrets to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets one by one:

| Secret Name | Value |
|------------|-------|
| `ACR_USERNAME` | Your ACR username |
| `ACR_PASSWORD` | Your ACR password |
| `VM_HOST` | Your VM's public IP address |
| `VM_USERNAME` | Your VM username (usually `azureuser`) |
| `VM_SSH_KEY` | Your SSH private key (entire content) |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `MYSQL_ROOT_PASSWORD` | Choose a secure password |
| `MYSQL_PASSWORD` | Choose a secure password |

### 5. Prepare Your Azure VM

SSH into your VM and install Docker (if not already done):

```bash
ssh azureuser@YOUR_VM_IP

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin -y

# Create app directory
sudo mkdir -p /home/azureuser/app
sudo chown -R azureuser:azureuser /home/azureuser/app

# Open firewall for port 8000
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

In Azure Portal:
1. Go to your VM → **Networking** → **Network settings**
2. Add inbound port rule for port **8000**

### 6. Test the Workflow

Push any change to trigger the workflow:

```bash
wsl git add .
wsl git commit -m "Test GitHub Actions"
wsl git push origin main
```

### 7. Monitor the Workflow

1. Go to your GitHub repo
2. Click **Actions** tab
3. You'll see your workflow running
4. Click on it to see live logs

## How It Works

```
Push to main → GitHub Actions triggers →
Build Docker image → Push to ACR →
SSH to VM → Pull image → Deploy with docker compose
```

## Troubleshooting

### Workflow fails at "Login to ACR"
- Check ACR_USERNAME and ACR_PASSWORD secrets
- Verify ACR admin user is enabled

### Workflow fails at "Deploy to Azure VM"
- Check VM_HOST, VM_USERNAME, VM_SSH_KEY secrets
- Verify VM allows SSH (port 22)
- Test SSH manually: `ssh -i your_key azureuser@VM_IP`

### Can't access app after deployment
- Check VM firewall: `sudo ufw status`
- Check Azure Network Security Group allows port 8000
- Check containers: `sudo docker ps`
- Check logs: `cd /home/azureuser/app && sudo docker compose logs -f`

## Useful Commands on VM

```bash
# Check running containers
sudo docker ps

# View logs
cd /home/azureuser/app
sudo docker compose logs -f

# Restart app
sudo docker compose restart

# Stop app
sudo docker compose down

# Manual pull and restart
sudo docker pull orchestrationAgent.azurecr.io/chatgpt-web-ui:latest
sudo docker compose up -d
```

## Benefits of GitHub Actions

- ✅ **FREE** - 2000 minutes/month for private repos, unlimited for public
- ✅ **No setup needed** - Runners are ready to use
- ✅ **Simple** - Just add secrets and push
- ✅ **Fast** - Usually starts within seconds

Your app will be live at: **http://YOUR_VM_IP:8000**
