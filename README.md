# DevSecOps virtualized training lab

This repository defines a disposable four-node DevSecOps training lab for a
Windows 11 host running VirtualBox:

| Node | Purpose | Services |
| --- | --- | --- |
| `gitlab` | GitLab GUI and registry | HTTP `80`, HTTPS `443`, SSH `2222` |
| `runner` | GitLab CI runner host | Docker and GitLab Runner |
| `app` | Vulnerable application target | Django `8000`, WebGoat `8080` |
| `jumpbox` | Security-testing workstation | Ansible, Nmap, Nikto, jq |

The VMs use DHCP. Do not assume or commit a lab IP address. Vagrant generates
runtime SSH settings and `scripts\Write-RuntimeInventory.ps1` converts them into
`ansible\inventory\runtime.yml`.

## 1. Install the host prerequisites

Open **elevated PowerShell** in the repository root. The repository does not
assume that VirtualBox, Vagrant, Python, or Ansible are already installed.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Install-HostDependencies.ps1 -InstallMissing
```

The `-InstallMissing` option uses WinGet for VirtualBox, Vagrant, and Python.
If an installer updates `PATH`, close and reopen PowerShell, then run the
command again without `-InstallMissing` to confirm the tools are visible.

The script creates the repository-local `.venv` and installs the pinned
Ansible Core version from `requirements.txt`; it does not install Ansible into
the system Python. The environment is ignored by Git.

To use the environment interactively after setup:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
ansible --version
```

Activation is optional for the repository scripts because they invoke the
executables directly from `.venv`.

## 2. Start and provision the lab

Run the full bootstrap:

```powershell
.\scripts\Start-Lab.ps1
```

This performs the following:

1. Creates or starts the `gitlab`, `runner`, `app`, and `jumpbox` VMs.
2. Generates `ansible\inventory\runtime.yml` from Vagrant's runtime SSH config.
3. Installs the baseline packages and Docker.
4. Starts the GitLab, GitLab Runner, Django, and WebGoat containers.
5. Installs the Jump Box security tools.

To create the VMs and generate the runtime inventory without applying Ansible:

```powershell
.\scripts\Start-Lab.ps1 -ProvisionOnly
```

To inspect the generated runtime inventory:

```powershell
Get-Content .\ansible\inventory\runtime.yml
```

The generated `ansible_host` and `ansible_port` values are ephemeral. Regenerate
the inventory after recreating VMs or whenever Vagrant's SSH configuration
changes.

## 3. Check VM state and connect to nodes

From the repository root:

```powershell
vagrant status
vagrant ssh gitlab
vagrant ssh runner
vagrant ssh app
vagrant ssh jumpbox
```

Inside a VM, leave the session with `exit`.

To discover the current private-network address of a node:

```powershell
vagrant ssh gitlab -c "hostname -I"
vagrant ssh runner -c "hostname -I"
vagrant ssh app -c "hostname -I"
vagrant ssh jumpbox -c "hostname -I"
```

Use the address returned at runtime. Do not replace it with a fixed address in
playbooks or documentation.

## 4. Interact with the services

The current Vagrantfile does not publish application ports to the Windows
host. Use either a node's runtime private-network address from the host, when
that address is reachable from Windows, or run the checks from inside a VM.

### GitLab

From the `gitlab` VM:

```bash
curl -I http://127.0.0.1
```

From a browser on the Windows host, use:

```text
http://<runtime-gitlab-address>
```

The development default root password is `ChangeMeLab123!`. Supply a different
value during provisioning instead of keeping the default:

```powershell
.\.venv\Scripts\ansible-playbook.exe `
  -i .\ansible\inventory\runtime.yml `
  .\ansible\playbooks\site.yml `
  --extra-vars "gitlab_initial_root_password=<strong-password>"
```

### Django and WebGoat

From the `app` VM:

```bash
curl http://127.0.0.1:8000
curl -I http://127.0.0.1:8080
```

From the Windows host, use the runtime app address:

```text
http://<runtime-app-address>:8000
http://<runtime-app-address>:8080/WebGoat
```

WebGoat is intentionally vulnerable and should only be used on this isolated
training network.

### GitLab Runner

Runner registration remains a manual lab exercise:

1. Open GitLab and sign in as the root user.
2. Create a project or group runner and copy its registration/authentication
   token.
3. Connect to the runner VM:

   ```powershell
   vagrant ssh runner
   ```

4. Register the runner against the runtime GitLab URL:

   ```bash
   docker exec -it devsecops-runner gitlab-runner register
   ```

5. Select the Docker executor when prompted and use `docker:latest` as the
   default image for basic CI exercises.

The runner container and registration instructions are also stored at
`/opt/devsecops-runner/README.txt`.

## 5. Run security testing from the Jump Box

Connect to the Jump Box:

```powershell
vagrant ssh jumpbox
```

The Jump Box contains Ansible, Nmap, Nikto, Python tooling, and jq. Use the
runtime app address discovered in the previous section:

```bash
nmap -sV <runtime-app-address> -p 8000,8080
nikto -h http://<runtime-app-address>:8000
nikto -h http://<runtime-app-address>:8080
```

The repository security playbook can also check the Django endpoint. From the
host, where the generated inventory is available, run:

```powershell
.\.venv\Scripts\ansible-playbook.exe `
  -i .\ansible\inventory\runtime.yml `
  .\ansible\playbooks\security-testing.yml `
  --extra-vars "app_host=<runtime-app-address>"
```

The playbook deliberately uses `hosts: localhost` and `connection: local` for
the testing action. This avoids creating an SSH hop when the test is executed
inside the Jump Box.

## 6. Stop, restart, and remove the lab

Stop the VMs while keeping their disks:

```powershell
vagrant halt
```

Start them again and reapply configuration if needed:

```powershell
.\scripts\Start-Lab.ps1
```

Remove the disposable VMs and their disks:

```powershell
vagrant destroy -f
```

After destruction, run the full installation and startup workflow again. The
runtime addresses and generated inventory may change.
