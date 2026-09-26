# frozen_string_literal: true

VAGRANT_BOX = "bento/ubuntu-22.04"

Vagrant.configure("2") do |config|
  config.vm.box = VAGRANT_BOX
  # Avoid an online box-version check on every `vagrant up`. Update deliberately
  # with `vagrant box update` when desired.
  config.vm.box_check_update = false
  # VMware boots extremely fast on Windows 11 Hyper-V engines, but a healthy 
  # timeout prevents unexpected SSH handshaking drops.
  config.vm.boot_timeout = 600
  config.vm.synced_folder ".", "/opt/devsecops-lab", disabled: true
  config.ssh.insert_key = true

  nodes = {
    # Total reservation: 22 GiB / 10 vCPUs. 
    # Leaves a perfect 10 GiB RAM / 6 CPU thread buffer for Windows 11 host operations.
    "gitlab"  => { memory: 8192, cpus: 4 }, # Shifted resources here for heavy DB operations
    "runner"  => { memory: 5120, cpus: 4 }, # Extra RAM to run heavy ZAP scans safely
    "app"     => { memory: 4096, cpus: 1 }, # Headroom for Django test suites
    "jumpbox" => { memory: 4096, cpus: 2 }  # Desktop session and browser for lab management
  }

  nodes.each do |name, resources|
    config.vm.define name do |node|
      node.vm.hostname = name
      node.vm.network "private_network", type: "dhcp"
      
      # Configure VMware Workstation Pro Engine
      node.vm.provider "vmware_desktop" do |v|
        v.memory = resources[:memory]
        v.cpus = resources[:cpus]
        v.linked_clone = true
        v.gui = name == "jumpbox"
        
        # Keep the VMware console available for the graphical jumpbox.
        v.vmx["gui.restrict"] = name == "jumpbox" ? "FALSE" : "TRUE"
        v.vmx["mks.enable3d"] = "FALSE"       # Disables unnecessary 3D graphic rendering 
        v.vmx["logging"] = "FALSE"            # Reduces disk write operations
      end
    end
  end
end
