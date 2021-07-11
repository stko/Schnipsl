sudo groupadd docker
sudo usermod -aG docker ${USER}
# You would need to log out and log back in so that your group membership is re-evaluated or type the following command:
su -s ${USER}

sudo apt -y update
sudo apt -y upgrade
sudo apt install -y docker docker-compose tmux git pip3 nodejs npm 

docker pull jonashaag/webfsd
docker tag 5b489e7273f1  webfsd:latest
