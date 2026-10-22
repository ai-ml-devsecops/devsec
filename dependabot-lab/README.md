# Dependabot Core development VM

This separate Ubuntu VM keeps the Dependabot checkout and Docker images outside
the four-node training lab. `Start-Lab.ps1` restores that lab's snapshots on
normal starts, so do not keep the checkout on its jumpbox. The VM is headless;
Windows runs VS Code and connects over SSH.

## First run

Finish any current `Start-Lab.ps1` run. The training lab reserves 22 GiB of RAM;
stop it before starting this 8 GiB VM. From the `devsec` repository root in
PowerShell:

```powershell
vagrant halt
cd .\dependabot-lab
vagrant up --provider=vmware_desktop
vagrant ssh -c "docker version --format '{{.Server.Version}}'"
vagrant ssh
```

The Vagrant provisioner installs Git and Docker and puts `vagrant` in the Docker
group. The fresh `vagrant ssh` login picks up that membership. In the Ubuntu VM:

```bash
git clone https://github.com/ai-ml-devsecops/dependabot-core.git
cd dependabot-core
git remote add upstream https://github.com/dependabot/dependabot-core.git
git remote -v
git rev-parse HEAD
bin/docker-dev-shell go_modules
```

On later logins, run `bin/docker-dev-shell` from the checkout root. If your
prompt ends in `~/dependabot-core/dry-run`, return to the root first:

```bash
cd ~/dependabot-core
bin/docker-dev-shell go_modules
```

The first development-shell run downloads or builds large Docker images and can
take a while. It mounts the checkout into the container, so Ruby source edits in
the VM are visible on the next run. At the `[dependabot-core-dev]` prompt, run
a reproducible public example and save its output:

```bash
set -o pipefail
bin/dry-run.rb go_modules rsc/quote 2>&1 | tee dry-run/go_modules-rsc-quote.log
exit
git rev-parse HEAD | tee dry-run/go_modules-rsc-quote.sha
```

The dry-run fetches manifests, parses dependencies, checks available versions,
and prints candidate changes without opening a pull request. Use `--dir` for a
manifest below the repository root and `--dep=NAME` to focus on one dependency.
Save the checkout SHA, command, and log together when comparing decisions. For
private repositories, use a token with only the access needed for the target
repository; do not put it in the checkout or a logged command.

## VS Code from Windows

From `dependabot-lab` in PowerShell, generate the SSH configuration after the VM
has booted or been recreated:

```powershell
vagrant ssh-config --host dependabot-core | Set-Content -Encoding ascii .vagrant\ssh-config
ssh -F .vagrant\ssh-config dependabot-core hostname
```

Install the VS Code **Remote - SSH** and **Dev Containers** extensions. Set the
VS Code user setting `remote.SSH.configFile` to the absolute path of
`dependabot-lab\.vagrant\ssh-config`, then run **Remote-SSH: Connect to Host**
and select `dependabot-core`. Open `/home/vagrant/dependabot-core`. To debug
inside Dependabot's container, run **Dev Containers: Reopen in Container** and
use the upstream **Debug Dry Run** F5 configuration. Regenerate the SSH config
after `vagrant destroy` and `vagrant up`, because Vagrant can replace its key or
forwarded port.

## Keep the fork and VM checkout current

Before a new investigation, use **Sync fork → Update branch** on the
[`ai-ml-devsecops/dependabot-core` fork](https://github.com/ai-ml-devsecops/dependabot-core),
or use `gh repo sync ai-ml-devsecops/dependabot-core -b main` from an
authenticated terminal. Do not force a sync if GitHub reports diverging commits.
Then, inside the VM:

```bash
cd ~/dependabot-core
git status --short
git switch main
git pull --ff-only origin main
git fetch upstream main
git rev-parse HEAD
git rev-parse upstream/main
```

The last two SHAs should match after a completed fork sync. Keep experiments on
their own branches so `main` remains easy to fast-forward. Record `git rev-parse
HEAD` beside each dry-run log; update the fork and checkout deliberately before
the next run. Rebuild the development image with `bin/docker-dev-shell
go_modules --rebuild` when upstream image definitions or native helpers change.

From `dependabot-lab` on Windows, stop and resume this VM with `vagrant halt`
and `vagrant up --provider=vmware_desktop`. This does not invoke the training
lab's snapshot restore. Check free disk space in the VM with `df -h` before
building multiple ecosystem images.

Sources: [Dependabot development guide](https://github.com/dependabot/dependabot-core#development-guide),
[GitHub fork sync](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/syncing-a-fork),
[Vagrant SSH config](https://developer.hashicorp.com/vagrant/docs/cli/ssh_config),
[VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh).
