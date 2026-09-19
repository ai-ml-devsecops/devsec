# ??? DevSecOps Training Lab

This repository defines a disposable four-node DevSecOps training lab for a Windows 11 host running VirtualBox.

## ?? Lab Topology
| Node | Role | Purpose | Services |
| --- | --- | --- | --- |
| `gitlab` | **SCM & CI/CD** | Source code, Pipelines, Registry | GitLab CE |
| `runner` | **Worker** | Executes CI/CD jobs | GitLab Runner |
| `app` | **Target** | Intentionally vulnerable apps | Django, WebGoat |
| `jumpbox` | **Workstation** | Security testing & management | Ansible, Nmap, Nikto |

## ?? Reproduction Guide (Step-by-Step)

### 1. Boot the Environment
Open an elevated PowerShell terminal in the project root:
```powershell
vagrant up
```

### 2. Install the Engine (Docker)
Since we are using a lean setup, Docker must be installed on the nodes. Run this for every node (`gitlab`, `app`, `runner`, `jumpbox`):
```powershell
vagrant ssh <node_name> -c "sudo apt-get update && sudo apt-get install -y docker.io"
```

### 3. Deploy the Services
Run these commands to launch the platforms as containers:

**GitLab Server:**
```powershell
vagrant ssh gitlab -c "sudo docker run -d --name gitlab -p 80:80 -p 443:443 -p 2222:22 gitlab/gitlab-ce:latest"
```

**Vulnerable App (WebGoat):**
```powershell
vagrant ssh app -c "sudo docker run -d --name webgoat -p 8080:8080 webgoat/webgoat"
```

### 4. Accessing the Lab
Get the IP addresses:
```powershell
vagrant ssh gitlab -c "hostname -I"
vagrant ssh app -c "hostname -I"
```

**URLs:**
*   **GitLab:** `http://<gitlab-ip>`
*   **WebGoat:** `http://<app-ip>:8080/WebGoat`

**GitLab Initial Password:**
```powershell
vagrant ssh gitlab -c "sudo docker exec gitlab grep 'Password:' /etc/gitlab/initial_root_password"
```

## ??? Jump Box Usage
The Jump Box is your attack station. You can run security tools as disposable containers:
```powershell
vagrant ssh jumpbox
# Inside Jump Box:
sudo docker run --rm nikto -h http://<app-ip>:8080
```

## ?? Hardware Requirements
To prevent "Zombie" freezes, the following allocation is recommended in the `Vagrantfile`:
*   **GitLab:** 12GB RAM / 4 CPUs
*   **Others:** 4GB RAM / 2 CPUs
