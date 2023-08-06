#!/bin/bash
 sudo hostnamectl set-hostname sorrentum_airfl
 sudo apt update
 echo "ubuntu  ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/ubuntu
 sudo apt-add-repository ppa:ubuntu/sorrentum_airfl
 sudo su - ubuntu
 mkkdir sor_eme && cd sor_eme && git init
 sudo ufw disable
 export AIRFLOW_UID=$(id -u)