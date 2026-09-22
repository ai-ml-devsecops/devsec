# frozen_string_literal: true

VAGRANT_BOX = "bento/ubuntu-22.04"

Vagrant.configure("2") do |config|
  config.vm.box = VAGRANT_BOX
  # Avoid an online box-version check on every `vagrant up`. Update deliberately
  # with `vagrant box update` when desired.
  config.vm.box_check_update = false
  # Cold boots can still be slow on a laptop; this avoids a false SSH failure
  # while preserving a usable amount of RAM for the Windows host.
  config.vm.boot_timeout = 900
  config.vm.synced_folder ".", "/opt/devsecops-lab", disabled: true
  config.ssh.insert_key = true

  nodes = {
    # Total reservation: 16 GiB / 8 vCPUs. This leaves sufficient RAM for
    # Windows, VirtualBox, and scans running inside the lab.
    "runner" => { memory: 3072, cpus: 2 },
    "app" => { memory: 2048, cpus: 1 },
    "jumpbox" => { memory: 3072, cpus: 2 }
  }

  nodes.each do |name, resources|
    config.vm.define name do |node|
      node.vm.hostname = name
      node.vm.network "private_network", type: "dhcp"
      node.vm.provider "virtualbox" do |vb|
        vb.name = "devsecops-#{name}"
        vb.memory = resources[:memory]
        vb.cpus = resources[:cpus]
        vb.linked_clone = true
        # These headless infrastructure VMs do not need a recorded desktop;
        # recording adds avoidable host CPU and disk activity.
        vb.customize ["modifyvm", :id, "--recording", "off"]
        # Vagrant accesses guests over SSH; disable the inherited VRDE server
        # that otherwise competes for the same localhost port on every VM.
        vb.customize ["modifyvm", :id, "--vrde", "off"]
      end
    end
  end
end
