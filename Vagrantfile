# -*- mode: ruby -*-
# vi: set ft=ruby :
 
host_path_dev      = "."
 
vm_path_dev        = "/app/src/chatbot/chatbot"
 
Vagrant.configure(2) do |config|
  config.vm.provider "virtualbox" do |v|
    v.cpus = 1
    v.memory = 1024
  end
 
  config.vm.box = "ubuntu/trusty64"
 
  config.vm.network "private_network", ip: "192.168.33.58"
 
  config.vm.host_name = "chatbot.dev"
 
  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder host_path_dev, vm_path_dev
 
end
