# frozen_string_literal: true

VAGRANT_BOX = "bento/ubuntu-22.04"

Vagrant.configure("2") do |config|
  config.vm.box = VAGRANT_BOX
  config.vm.synced_folder ".", "/opt/devsecops-lab", disabled: true
  config.ssh.insert_key = true

  nodes = {
    "gitlab" => { memory: 12288, cpus: 4 },
    "runner" => { memory: 4096, cpus: 2 },
    "app" => { memory: 3072, cpus: 2 },
    "jumpbox" => { memory: 4096, cpus: 2 }
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
      end
    end
  end
end
