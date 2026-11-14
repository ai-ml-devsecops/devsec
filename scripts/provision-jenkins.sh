#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl fontconfig git openjdk-21-jre podman uidmap slirp4netns fuse-overlayfs

install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key -o /etc/apt/keyrings/jenkins-keyring.asc
echo 'deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/' > /etc/apt/sources.list.d/jenkins.list
apt-get update
apt-get install -y jenkins
systemctl stop jenkins
if ! grep -q '^jenkins:' /etc/subuid; then usermod --add-subuids 200000-265535 jenkins; fi
if ! grep -q '^jenkins:' /etc/subgid; then usermod --add-subgids 200000-265535 jenkins; fi

install -d -o jenkins -g jenkins -m 0755 /var/lib/jenkins/plugins

curl -fsSL https://github.com/jenkinsci/plugin-installation-manager-tool/releases/download/2.16.0/jenkins-plugin-manager-2.16.0.jar -o /tmp/jenkins-plugin-manager.jar
java -jar /tmp/jenkins-plugin-manager.jar \
  --war /usr/share/java/jenkins.war \
  --plugin-download-directory /var/lib/jenkins/plugins \
  --plugins workflow-aggregator git gitlab-plugin credentials-binding ssh-credentials
chown -R jenkins:jenkins /var/lib/jenkins/plugins

install -d -o jenkins -g jenkins -m 0700 /var/lib/jenkins/run
install -d -o jenkins -g jenkins -m 0755 /var/lib/jenkins/.config/containers
cat > /var/lib/jenkins/.config/containers/containers.conf <<'EOF'
[engine]
cgroup_manager = "cgroupfs"
EOF
chown jenkins:jenkins /var/lib/jenkins/.config/containers/containers.conf
install -d -m 0755 /etc/systemd/system/jenkins.service.d
cat > /etc/systemd/system/jenkins.service.d/lab.conf <<'EOF'
[Service]
Environment="XDG_RUNTIME_DIR=/var/lib/jenkins/run"
EOF
systemctl daemon-reload
systemctl enable jenkins
systemctl restart jenkins
for attempt in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8080/login >/dev/null; then break; fi
  sleep 5
done
curl -fsS http://127.0.0.1:8080/login >/dev/null

# Podman is daemonless. Jenkins builds use its own unprivileged user namespace.
cd /var/lib/jenkins
runuser -u jenkins -- env HOME=/var/lib/jenkins XDG_RUNTIME_DIR=/var/lib/jenkins/run podman info >/dev/null
