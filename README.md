# DevSecOps virtualized training lab

This repository defines a disposable four-node lab for Windows 11 and VirtualBox:

| Node | Purpose |
| --- | --- |
| `gitlab` | GitLab GUI and registry |
| `runner` | GitLab CI runner |
| `app` | Django/WebGoat training target |
| `jumpbox` | Local security-testing workstation |

The VMs use VirtualBox NAT networking and DHCP. No lab IP address is committed. The
bootstrap script generates an Ansible inventory from each VM's runtime SSH
configuration.

## Prerequisites

The host bootstrap is intentionally explicit. It checks for and documents the
required tools rather than assuming they exist:

- Windows 11
- VirtualBox 7.x
- Vagrant 2.4.x
- PowerShell 5.1 or newer
- Python 3.11+ and Ansible Core 2.16+ (installed in the repository virtual environment)

Run from an elevated PowerShell. On a clean Windows host, `-InstallMissing`
uses WinGet for VirtualBox, Vagrant, and Python; a new terminal may be required
after those installers update `PATH`:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Install-HostDependencies.ps1 -InstallMissing
.\scripts\Start-Lab.ps1
```

`Start-Lab.ps1` runs the host bootstrap and then invokes the top-level Ansible
playbook. It does not start nested `ansible-playbook` processes from Ansible.

To tear down the disposable environment:

```powershell
vagrant destroy -f
```

## Lab phases

Phase 1 provisions the VMs and installs their baseline services. Phase 2 is run
from the Jump Box:

```bash
cd /opt/devsecops-lab/ansible
ansible-playbook -i inventory/runtime.yml playbooks/security-testing.yml \
  --extra-vars "app_host=<runtime-app-address>"
```

The runtime address is supplied by the generated inventory or `--extra-vars`;
the playbooks never embed a static lab address.
