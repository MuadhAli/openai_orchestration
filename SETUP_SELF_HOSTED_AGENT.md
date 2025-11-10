# Setup Self-Hosted Azure DevOps Agent

This guide will help you set up a self-hosted agent on your Azure VM to run pipelines for FREE (no parallelism needed).

## Why Self-Hosted Agent?
- **FREE** - No need to wait for Microsoft's parallelism approval
- **Faster** - Builds run on your own VM
- **More control** - Full access to your environment

## Setup Steps

### 1. SSH into Your Azure VM

```bash
ssh azureuser@YOUR_VM_IP
```

### 2. Install Prerequisites

```bash
# Update system
sudo apt-get update

# Install required packages
sudo apt-get install -y curl wget tar libicu-dev

# Verify Docker is installed (should already be from earlier setup)
docker --version
```

### 3. Download Azure Pipelines Agent

```bash
# Create agent directory
mkdir -p ~/myagent && cd ~/myagent

# Download the latest agent (check for latest version at https://github.com/microsoft/azure-pipelines-agent/releases)
wget https://vstsagentpackage.azureedge.net/agent/3.236.1/vsts-agent-linux-x64-3.236.1.tar.gz

# Extract
tar zxvf vsts-agent-linux-x64-3.236.1.tar.gz
```

### 4. Get Your Azure DevOps Personal Access Token (PAT)

1. Go to Azure DevOps (https://dev.azure.com)
2. Click your profile icon (top right) → **Personal access tokens**
3. Click **+ New Token**
4. Settings:
   - **Name:** "Self-Hosted Agent"
   - **Organization:** Select your organization
   - **Expiration:** 90 days (or custom)
   - **Scopes:** Select **"Agent Pools (read, manage)"** and **"Deployment Groups (read, manage)"**
5. Click **Create**
6. **COPY THE TOKEN** - You won't see it again!

### 5. Configure the Agent

```bash
cd ~/myagent

# Run configuration
./config.sh
```

**You'll be prompted for:**

1. **Server URL:** `https://dev.azure.com/YOUR_ORGANIZATION`
   - Replace YOUR_ORGANIZATION with your actual org name
   
2. **Authentication type:** Press Enter (PAT is default)

3. **Personal access token:** Paste the PAT you created

4. **Agent pool:** Press Enter (uses "Default" pool)

5. **Agent name:** Press Enter (uses hostname) or type a custom name

6. **Work folder:** Press Enter (uses default _work)

7. **Run agent as service:** Type `Y` and press Enter

8. **User account:** Press Enter (uses current user)

### 6. Install and Start the Agent Service

```bash
# Install as service
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

### 7. Verify Agent is Online

1. Go to Azure DevOps
2. Click **Project Settings** (bottom left)
3. Click **Agent pools** under "Pipelines"
4. Click **Default** pool
5. Click **Agents** tab
6. You should see your agent listed as **Online** (green)

### 8. Grant Agent Permissions

1. In the **Default** pool, click **Security** tab
2. Find your project
3. Make sure it has **"User"** role (should be automatic)

## Test the Pipeline

Now commit and push your updated pipeline:

```bash
cd /path/to/your/project

git add azure-pipelines.yml
git commit -m "Switch to self-hosted agent"
git push azure main
```

The pipeline should now run on your self-hosted agent!

## Troubleshooting

### Agent shows offline
```bash
# Check service status
sudo ./svc.sh status

# Restart service
sudo ./svc.sh stop
sudo ./svc.sh start

# Check logs
cd ~/myagent
cat _diag/*.log
```

### Permission denied errors
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Restart agent
sudo ./svc.sh restart
```

### Agent not picking up jobs
- Make sure the pool name in `azure-pipelines.yml` matches your agent pool (Default)
- Check agent capabilities in Azure DevOps → Agent pools → Default → Agents → Your agent → Capabilities

## Useful Commands

```bash
# Check agent status
sudo ./svc.sh status

# Stop agent
sudo ./svc.sh stop

# Start agent
sudo ./svc.sh start

# Restart agent
sudo ./svc.sh restart

# Uninstall agent service
sudo ./svc.sh uninstall

# View agent logs
cd ~/myagent
tail -f _diag/*.log
```

## Next Steps

Once your agent is online and the pipeline runs successfully:
1. The agent will build your Docker image
2. Push it to ACR
3. Deploy it to the same VM (localhost)

This is actually more efficient since everything runs on the same machine!
