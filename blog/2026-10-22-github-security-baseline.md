---
title: "GitHub security checks for a DevSecOps lab"
date: 2026-10-22
description: "Configure dependency alerts, review scanner findings, and prepare a VMware training lab repository for public release."
---

# GitHub security checks for a DevSecOps lab

This guide follows the security review of a four-node Vagrant and VMware training lab before public release. Initial scans ran while the repository was private. At publication, the repository is public and eligible for free GitHub code scanning. The initial findings below describe the reviewed configuration; remediation steps are not claims of completed fixes.

## 1. Enable dependency monitoring and scans

Commit these files and push them to GitHub:

| File | Purpose |
| --- | --- |
| `.github/dependabot.yml` | Scheduled Python and GitHub Actions version updates. |
| `.github/workflows/security.yml` | Trivy, Checkov, CodeQL, and container image scans. |
| `GH/requirements-scan.txt` | Pinned Checkov dependency. |

In repository security settings, enable the dependency graph, Dependabot alerts, security updates, and malware alerts. Version updates are configured separately in `dependabot.yml`.

**insert photo here**

*Image description: Repository security settings showing the dependency graph, Dependabot alerts, security updates, and malware alerts enabled.*

Open **Actions → Security baseline → a run → Open-source repository scans**. Inspect the Trivy and Checkov steps and download `security-scan-reports-<run ID>`. PR titles describe the change that triggered the workflow, not the scanner running inside it. Container scans require a scheduled or manually triggered run.

A successful workflow does not establish that findings were resolved: Trivy uses `exit-code: "0"`, Checkov uses `--soft-fail`, and SARIF uploads allow errors without failing the job.

**insert photo here**

*Image description: A Security baseline run expanded to show Trivy and Checkov steps and its downloadable scan-report artifact.*

## 2. Prioritize the Ansible fix

The initial Trivy report identified `ansible-core==2.16.14` in `requirements.txt`. [CVE-2026-11332](https://github.com/advisories/GHSA-w8p5-mx5w-cpqj) permits code execution on the machine installing a malicious role through `ansible-galaxy role install`.

No `ansible-galaxy` invocation was found in the tracked project files reviewed. That limits the demonstrated exposure in the current provisioning path, but does not make the vulnerable dependency safe. The jumpbox controller holds lab SSH keys, making controller compromise consequential even inside a VM.

Prioritize PR #2, which proposed `2.21.5`, but merge only after checking Python compatibility and testing provisioning. That version is above the advisory's patched threshold for its branch. The listed `2.16.19rc1` is a patched boundary, not a requirement to install that release candidate. If the larger upgrade is incompatible, select a compatible patched stable release and document any interim support limitations.

The host requirements pin and the controller installation are separate: `scripts/Start-Lab.ps1` installs Ansible through Ubuntu's package manager on the jumpbox. Merging the requirements change alone does not update that controller. Check the actual runtime from PowerShell in the repository root:

```powershell
vagrant ssh jumpbox -c "ansible --version; python3 --version; apt-cache policy ansible-core"
```

Check distribution security patches as well as the package version. Update the controller through a reproducible installation path, then test the playbooks. Compare runtime requirements against the [Ansible support matrix](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html).

The initial PRs came from version checks; the Ansible PR subsequently linked to a security alert. Review Playwright PR #1 and Trivy action PR #3 separately, checking upstream changes, action commit pins, and their affected workflows before merging. A version-update PR can also resolve a vulnerability.

**insert photo here**

*Image description: The Ansible vulnerability alert with its linked PR and the message that merging the PR would fix the alert. Use the resolved state only after remediation is verified.*

## 3. Address HTTP paths without replacing working TLS unnecessarily

The app role already configures Nginx on HTTPS port 443 using a self-signed certificate. Checkov flags the application test because it requests `http://<app>:8000`, bypassing Nginx entirely. The warning concerns that HTTP URL, not the certificate issuer.

| Reviewed configuration | Recommended action |
| --- | --- |
| `ansible/playbooks/security-testing.yml` calls HTTP port 8000. | Change the normal health check to the existing HTTPS endpoint after configuring client trust. |
| `ansible/roles/jumpbox/tasks/main.yml` generates another HTTP check. | Update the generated check too, so reprovisioning preserves the fix. |
| App Docker mapping is `8000:8000`. | Bind the backend to `127.0.0.1:8000:8000` and recreate the container so remote clients use Nginx. Retain direct HTTP only for an explicitly isolated exercise. |
| Certificate generation supplies a CN but no explicit Subject Alternative Name. | Generate a certificate with a SAN matching the hostname or IP used by clients, and distribute its trust certificate or lab CA to the jumpbox. Keep certificate validation enabled. |
| GitLab readiness and token checks use `http://localhost`. | Document narrow Checkov exceptions if intentional. These requests originate inside the GitLab VM and reach its locally published container port; they do not traverse the inter-VM network. |

A publicly issued certificate is unnecessary for this lab. A properly trusted lab certificate can support verified HTTPS. Changing URLs alone may cause certificate-validation failures. Disabling validation would leave server identity unchecked.

VM isolation separates operating systems, but the nodes deliberately communicate over a private virtual network. It does not encrypt HTTP or prevent a compromised node from accessing reachable services. Actual exposure also depends on VMware networking, routing, and firewall rules; the Vagrantfile alone cannot prove isolation.

For the homelab, prioritize the cross-VM application check and backend restriction. The localhost exceptions can remain with a documented rationale. Separately, GitLab's external URL, runner registration, and registry also use HTTP. Use TLS for those credential-bearing inter-VM paths, or explicitly restrict them to a disposable isolated exercise with lab-only credentials. The three Checkov findings are not a complete inventory of transport risks.

## 4. Review SARIF against the matching source

From PowerShell in the repository root, using an authenticated GitHub CLI:

```powershell
gh run list --workflow security.yml --limit 10
$runId = Read-Host "Run ID from the list"
gh run view $runId --verbose
gh run download $runId --name "security-scan-reports-$runId" --dir "$env:LOCALAPPDATA\devsec\scan-reports\$runId"
```

Keep the repository open in VS Code. Run **SARIF: Show Panel** and load `trivy-results.sarif` or `checkov-results/results_sarif.sarif`. If prompted to locate a source file, select the corresponding file in the repository. Match the scanned commit for accurate line locations. Keep reports outside tracked files; artifacts expire after 14 days.

Under **Security → Dependabot → Malware**, no alerts were shown during the initial review. This means no matching malware alerts were displayed, not that arbitrary repository code was proven malware-free.

## 5. Complete the public-release checks

Before changing visibility:

1. Resolve the Ansible manifest and controller findings, test provisioning, and rerun the scans.
2. Implement the normal HTTPS app path and document intentional training exceptions. Verify network exposure from the host and another lab VM.
3. Replace the GitLab role's hard-coded fallback password with a required externally supplied secret. Rotate it on existing instances if used. Protect token-handling Ansible tasks with `no_log` and review generated output for credentials.
4. Scan tracked files and full Git history for credentials and private keys. The current Trivy filesystem scan does not establish that history is clean, even with a full checkout. Review reports and screenshots before publication, and revoke any exposed credentials.
5. Run the manual container scans and triage their findings. Preserve intentional vulnerabilities in the training target only with clear isolation requirements. Do not treat infrastructure vulnerabilities as necessary training content.

Once the repository is public, trigger a fresh run:

```powershell
gh workflow run security.yml --ref master
gh run list --workflow security.yml --limit 5
```

During the private phase, this workflow skipped CodeQL and publishing findings because private code scanning was not enabled under an eligible plan. [Public repositories can use code scanning without that paid requirement](https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning). The existing workflow conditions permit CodeQL and SARIF uploads on new public-repository runs. Verify both Python and Ruby analysis, inspect upload steps for warnings, and confirm results under **Security → Code scanning**. Verify secret scanning and push protection are enabled as well.

**insert photo here**

*Image description: After public release and a fresh successful scan, the Code scanning tool status showing CodeQL, Trivy, and Checkov analyses. Include remaining documented findings rather than implying the repository is free of all risks.*
