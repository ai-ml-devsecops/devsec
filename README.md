# DevSecOps Training Lab

This repository defines a disposable four-node DevSecOps training lab running natively over VMware Workstation Pro.

## Lab Topology

| Node | Role | Purpose | Services |
| --- | --- | --- | --- |
| `gitlab` | **SCM & CI/CD** | Source code, Pipelines, Registry | GitLab CE |
| `runner` | **Worker** | Executes CI/CD jobs | GitLab Runner |
| `app` | **Target** | Vulnerable Django Application | django.nv |
| `jumpbox` | **Workstation** | Security testing & management | Docker Tools |

## Setup & Execution Guide

### 1. Boot the Environment
From `C:\Users\ai-ml\projects-local\devsec` in an elevated PowerShell terminal, run:
```powershell
vagrant up --provider=vmware_desktop
```

### 2. Install the Engine (Docker)
Docker must be present across nodes. Run this installation logic for every node (`gitlab`, `app`, `runner`, `jumpbox`):
```powershell
vagrant ssh <node_name> -c "sudo apt-get update && sudo apt-get install -y docker.io"
```

### 3. Deploy Core Platforms

**GitLab Server:**
```powershell
vagrant ssh gitlab -c "sudo docker run -d --name gitlab -p 80:80 -p 443:443 -p 2222:22 gitlab/gitlab-ce:latest"
```

**Production Target (django.nv):**
```powershell
# Clone and spin up the target application directly on the app server
vagrant ssh app -c "git clone https://practical-devsecops.training && cd django.nv && sudo docker build -t django-app . && sudo docker run -d --name django_nv -p 8000:8000 django-app"
```

### 4. Lab Ingress & Credentials
Run `hostname -I` via Vagrant SSH to discover node IP addresses:
```powershell
vagrant ssh gitlab -c "hostname -I"
vagrant ssh app -c "hostname -I"
```

*   **GitLab Dashboard:** `http://<gitlab-ip>`
*   **Target Application:** `http://<app-ip>:8000`

**Fetch Root Password for GitLab:**
```powershell
vagrant ssh gitlab -c "sudo docker exec gitlab grep 'Password:' /etc/gitlab/initial_root_password"
```

## Security Evaluation (Jump Box)
Establish a session on your attack node to test the application target using containerized tools:
```powershell
vagrant ssh jumpbox

# Inside Jump Box container execution test:
sudo docker run --rm hysnsec/nikto -h http://<app-ip>:8000
```

## Environment Management
*   **Stop Workloads:** `vagrant halt`
*   **Wipe Lab Infrastructure:** `vagrant destroy -f`
