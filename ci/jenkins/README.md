# Jenkins lab VM

From the repository root:

```powershell
.\scripts\Provision-Jenkins.ps1
vagrant ssh jenkins -c "hostname -I; systemctl is-active jenkins"
```

Jenkins, Pipeline and GitLab plugins, Git, and rootless Podman are installed.
The VM does not create a job or a webhook. Create a Pipeline job in the Jenkins
UI, select **Pipeline script from SCM**, and point it at the application
repository on the lab GitLab VM. Put the `Jenkinsfile` in that repository's root.
Add the GitLab source credential and webhook manually as the lesson describes.

Both CI systems can reach the same app VM. Run deployments one at a time if
both pipelines are enabled.

The lesson assumes a configured GitLab connection and Docker-based stages. This
VM has the GitLab plugin and Podman; configure those prerequisites or adapt
the sample stages before running its full pipeline.
