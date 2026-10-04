# DevSecOps Training Lab

This repository defines a disposable four-node DevSecOps training lab running natively over VMware Workstation Pro.

## Lab Topology

| Node | Role | Purpose | Services |
| --- | --- | --- | --- |
| `gitlab` | **SCM & CI/CD** | Source code, Pipelines, Registry | GitLab CE |
| `runner` | **Worker** | Executes CI/CD jobs | GitLab Runner |
| `app` | **Target** | Vulnerable Django Application | django.nv |
| `jumpbox` | **Headless controller** | Security testing & management over SSH | Ansible, CLI tools |

## Setup & Execution Guide

### 1. One-time host setup
```powershell
.\scripts\Install-HostDependencies.ps1 -InstallMissing
```

### 2. Start the lab
```powershell
.\scripts\Start-Lab.ps1
```
On the first run this fully provisions the lab: boots the four VMs, runs the Ansible
playbooks (from `ansible/`, executed on the `jumpbox` node, which acts as the Ansible
controller since Windows cannot run `ansible-playbook` directly), deploys GitLab with
persistent storage, generates and validates an ephemeral API token, imports
`pdso/django.nv` with Auto DevOps enabled, registers a project runner, and triggers the
first pipeline run. It then snapshots all four VMs as `initial-ready`.

Subsequent runs restore that snapshot instead of re-provisioning, for a fast (~5-10 min)
start. Two switches control this:
*   `.\scripts\Start-Lab.ps1 -Reset` — revert to the `initial-ready` snapshot even if the
    lab is already running.
*   `.\scripts\Start-Lab.ps1 -Rebuild` — destroy the VMs and fully re-provision from
    scratch (use after changing the Vagrantfile, playbooks, or scripts).

### Restart a timed-out jumpbox

If `vagrant ssh jumpbox` hangs, press `Ctrl+C`, then force-restart only the jumpbox:
```powershell
.\scripts\Start-Lab.ps1 -RestartJumpbox
```

This does not restore or restart GitLab, runner, or app. The jumpbox runs without
a VMware window, desktop, display manager, or browser. Manage it through SSH and
open the GitLab and application URLs in your Windows browser.

Check connectivity:
```powershell
vagrant status jumpbox
vagrant ssh jumpbox -c "hostname; hostname -I"
```

### 3. Lab Ingress & Credentials
`Start-Lab.ps1` prints each node's IP address at the end of every run.

*   **GitLab Dashboard:** `http://<gitlab-ip>`
*   **GitLab project:** `http://<gitlab-ip>/pdso/django.nv`
*   **Target Application:** `http://<app-ip>:8000`

**Fetch the root password for GitLab:**
```powershell
vagrant ssh gitlab -c "sudo docker exec devsecops-gitlab grep 'Password:' /etc/gitlab/initial_root_password"
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
