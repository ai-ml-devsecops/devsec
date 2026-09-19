# ??? DevSecOps Lab User Guide

This guide provides the manual steps to boot, configure, and interact with the DevSecOps training lab.

## ?? Phase 1: Booting the Lab
From the repository root in PowerShell:

```powershell
# Power on all VMs
vagrant up

# Get the IP addresses of your nodes
vagrant ssh gitlab -c "hostname -I"
vagrant ssh app -c "hostname -I"
vagrant ssh jumpbox -c "hostname -I"
vagrant ssh runner -c "hostname -I"
```

## ?? Phase 2: Installing the "Engine" (Docker)
Each node needs Docker installed to run the services. Run this for **every** node (`gitlab`, `app`, `runner`, `jumpbox`):

```powershell
vagrant ssh <node_name> -c "sudo apt-get update && sudo apt-get install -y docker.io"
```

## ?? Phase 3: Deploying the Services

### ?? GitLab Server
Run this on the `gitlab` node to start the platform:
```powershell
vagrant ssh gitlab -c "sudo docker run -d --name gitlab -p 80:80 -p 443:443 -p 2222:22 gitlab/gitlab-ce:latest"
```
*   **URL:** `http://<gitlab-ip>`
*   **User:** `root`
*   **Password:** `ChangeMeLab123!`
*   *Note: GitLab takes 5-10 minutes to fully boot. If you see a "502" error, just wait and refresh.*

### ?? Production Target (WebGoat)
Run this on the `app` node to start the vulnerable target:
```powershell
vagrant ssh app -c "sudo docker run -d --name webgoat -p 8080:8080 webgoat/webgoat"
```
*   **URL:** `http://<app-ip>:8080/WebGoat`

## ??? Phase 4: Using the Jump Box (Attack Station)
The Jump Box is your workstation. You don't need to install tools permanently; you can run them as disposable containers.

**Connect to the Jump Box:**
```powershell
vagrant ssh jumpbox
```

**Example: Run Nikto against the App node:**
```bash
sudo docker run --rm nikto -h http://<app-ip>:8080
```

## ?? Phase 5: Lab Management

| Action | Command | Description |
| --- | --- | --- |
| **Stop** | `vagrant halt` | Shuts down VMs (Saves state to disk) |
| **Pause** | `vagrant suspend` | "Sleeps" the VMs (Fastest restart) |
| **Restart** | `vagrant up` | Powers on the machines |
| **Wipe** | `vagrant destroy -f` | Deletes everything (Fresh start) |

---
**Pro Tip:** If a VM becomes unresponsive ("Zombie state"), run `vagrant reload <node_name>` to hard-reset it.
