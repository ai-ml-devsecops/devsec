# DevSecOps Lab Deployment Guide (VMware Workstation Pro)

This document provides step-by-step instructions to initialize a clean Windows 11 host environment and deploy your local four-node training lab using VMware.

## Step 1: Install Host Hypervisor & Automation Tools
Open PowerShell as an Administrator and execute the following commands to install the required system binaries via Winget:
```powershell
# Install hypervisor, provisioning, and environment tools
winget install --id VMware.WorkstationPro --exact --accept-package-agreements
winget install --id Hashicorp.Vagrant --exact --accept-package-agreements
winget install --id Hashicorp.VagrantVMwareUtility --exact --accept-package-agreements
winget install --id Python.Python.3.11 --exact --accept-package-agreements
```
*Note: Restart your PowerShell terminal session after installation finishes to fully refresh your host's system PATH variables.*

## Step 2: Initialize Python Virtual Environment 
Navigate directly to your local project directory and set up your script dependencies:
```powershell
cd C:\Users\ai-ml\projects-local\devsec

# Build and populate local virtual environment
python -m venv .venv
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
```

## Step 3: Configure Scripts and Boot the Fleet
Run your validation scripts to confirm paths, then kick off the environment provision:
```powershell
# Verify system paths match VMware requirements
.\(\scripts\check-\)prereqs.ps1 -InstallMissing

# Boot the lab nodes using the VMware Desktop provider engine
vagrant up --provider=vmware_desktop

# Build host configurations (skip inventory deployment tasks for now)
.\scripts\generate-inventory.ps1 -OutputPath .\inventories\runtime-external.yml
```
