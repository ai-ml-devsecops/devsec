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
docker run --rm hysnsec/nikto -h http://<app-ip>:8000
```

Docker is installed and enabled automatically on the jump box. If Docker was
added after the current VM snapshot was created, run `.\scripts\Start-Lab.ps1 -Rebuild`
once to reprovision the node and refresh the snapshot.

## Environment Management
*   **Stop Workloads:** `vagrant halt`
*   **Wipe Lab Infrastructure:** `vagrant destroy -f`

## Preserving the lab across restarts

`Start-Lab.ps1` normally restores the `initial-ready` snapshot. After a
successful rebuild or any intentional VM-side configuration change, refresh
that snapshot once:

```powershell
.\scripts\Start-Lab.ps1 -RefreshSnapshot
```

After that, shutdowns and normal startups preserve the working configuration:

```powershell
.\scripts\Start-Lab.ps1
```

On a different laptop, clone the repository, install the host dependencies,
then run `Start-Lab.ps1 -Rebuild` once. The checked-in Ansible configuration
recreates the GitLab registry, runner, app Docker registry settings, and lab
network. Run `-RefreshSnapshot` after the rebuild.

Deployment credentials are intentionally not portable repository files. On a
new laptop, create a new SSH key, authorize its public key for the app VM's
`vagrant` user, and add the matching private key and verified app host key as
the GitLab project file variables `PROD_SSH_PRIVKEY` and `SSH_KNOWN_HOSTS`.
Leave both variables unprotected when using the default `main` branch unless
that branch is configured as protected.
