# AGENTS.md

## 🎯 Overview & Environment
DevSecOps virtualized training lab topology.
- **Host Layer:** Windows 11 with VirtualBox installed. Copilot runs via VS Code integrated Git terminal (`copilot`).
- **Target Topology:** Virtualized GitLab Runner, GitLab GUI, Django/WebGoat App, and a Jump Box.

## 🔄 Execution Phases
1. **Phase 1 (Bootstrap):** Bootstrapping the lab environment from the Windows host using automated virtualization tools.
2. **Phase 2 (Lab Testing):** Executing security testing playbooks directly from inside the virtualized Jump Box node.

## ⚠️ Engineering Boundaries
- **Zero Assumptions:** Do not assume Vagrant, Ansible, Python, or guest packages are pre-installed. Track all software dependencies and installation steps directly via version control.
- **Dynamic Routing:** Do not hardcode static IP addresses for the virtual lab nodes. Always account for ephemeral VM network addresses using runtime flags (`--extra-vars`) or dynamic tracking.
- **No CLI Nesting:** Do not use Ansible's `shell` or `command` modules to trigger `ansible-playbook` sub-processes. Use native play imports or task includes instead.
- **Local Handoff Connection:** When a playbook runs inside the Jump Box to configure its own local toolset, enforce `hosts: localhost` and `connection: local` to drop SSH connection overhead.
