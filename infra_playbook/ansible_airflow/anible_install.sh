#!/bin/bash
 sudo hostnamectl set-hostname ansible
  sudo apt update
   sudo adduser ansible
    echo "ansible  ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/ansible
     sudo apt-add-repository ppa:ansible/ansible
      sudo apt install ansible  -y
       sudo chown ansible -R  /etc/ansible/
        sudo su - ansible