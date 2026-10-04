# Manual GitLab lab pipeline

`lab-pipeline.yml` is a review template for the **django.nv application project**.
It is not installed, included by another pipeline, or wired into Ansible.

## Before running

- Provisioning configures GitLab's registry at `http://<gitlab-ip>:5050`, publishes
  port 5050, and enables the project registry. DinD and the app VM are configured
  to use this HTTP endpoint as an insecure registry. This is for the isolated lab
  only: registry credentials are not protected by TLS on the lab network. Use a
  trusted TLS certificate and CA configuration instead for production.
- The application's repository root must contain its working Dockerfile.
- The registered runner needs the privileged Docker executor for DinD.
- Authorize a dedicated deployment public key for the app VM's `vagrant` user.
  The corresponding private key must work without an interactive passphrase.
  Verify `sudo -n docker info` works for that user.
- Confirm the app IP; the template defaults to `192.168.26.143`.
- Nginx must already provide HTTPS on port 443, proxying to the app on 8000.
  This pipeline replaces the application container; it does not configure Nginx.

Set these project CI/CD variables in GitLab:

| Variable | Type | Value |
| --- | --- | --- |
| `PROD_SSH_PRIVKEY` | File | Deployment private key, with a final newline |
| `SSH_KNOWN_HOSTS` | File | App SSH host keys verified through a trusted connection |
| `PROD_HOSTNAME` | Variable, optional | App IP or DNS name; overrides the YAML default |
| `PROD_USERNAME` | Variable, optional | SSH user; defaults to `vagrant` |

Restrict deployment secrets to a protected default branch. Leave variable expansion
disabled for the key contents. GitLab supplies the `CI_REGISTRY_*` credentials;
do not put credentials into this file. Never commit the private key.

## Manual use after review

1. Copy the template into the application's `.gitlab-ci.yml` through GitLab's UI.
2. Validate it in GitLab's pipeline editor / CI Lint before committing.
3. Commit it to the default branch.
4. For a build-only check, temporarily set `prod` to `when: manual` in the project copy. Confirm the build pushes the image, then restore the job and run a full pipeline to test deploy and scans.
   The workflow excludes push, merge request, schedule, and API triggers for now.

The pipeline builds and pushes a commit-tagged image, pulls it onto the app VM,
replaces `devsecops-django`, waits for HTTP readiness, then runs the three scans.
Deployment causes brief downtime and has no automatic rollback. Run one complete
pipeline at a time: the deploy lock does not stop a later deployment during scans.

Reports are copied out of stopped scan containers before artifact upload, avoiding
reliance on shared bind-mount paths between the job and DinD service. Scan jobs have
`allow_failure: true`; inspect their logs and artifacts even if the pipeline is green.
Nmap explicitly checks ports 80, 443, and 8000. Scan images retain the names from the
working example; pin reviewed image versions or digests before standardizing this.
Docker 24.0.5 is retained to match the working lab example, not as a current-version
recommendation.

## Future jumpbox API scripts: proposed scope only

Running explicit scripts on the headless jumpbox is a sensible approach. Keep the
pipeline YAML in version control and keep GitLab project setup separate from VM
provisioning. No new API scripts are implemented in this change.

After reviewing the manual workflow, consider scripts under `scripts/gitlab/` that:

1. Read the GitLab URL, project path, and an API token from the environment; validate
   project access and report runner/registry readiness without printing secrets.
2. Default to a read-only plan showing existing versus requested project settings.
3. Apply only explicitly requested variable or repository-file changes, using the
   appropriate GitLab APIs and preserving unrelated settings.
4. Lint the reviewed pipeline, then optionally commit it on a review branch.
5. Trigger and monitor a pipeline only through a separate explicit command.

API-triggered runs would require an intentional change to the template's workflow
rules (currently UI-only). Registry endpoint and Docker daemon configuration are
host provisioning tasks; API bootstrap cannot replace that host configuration.
Review the existing bootstrap script before reuse: it also imports a project,
enables Auto DevOps, and can create runners, so it is broader than this workflow.

References:
- [GitLab CI YAML and CI Lint](https://docs.gitlab.com/ci/yaml/)
- [Docker-in-Docker](https://docs.gitlab.com/ci/docker/docker_in_docker/)
- [SSH keys and file variables](https://docs.gitlab.com/ci/jobs/ssh_keys/)
- [Container registry setup](https://docs.gitlab.com/administration/packages/container_registry/)
