sudo groupadd docker
sudo usermod -aG docker ${USER}
# You would need to log out and log back in so that your group membership is re-evaluated or type the following command:
su -s ${USER}

sudo apt -y update
sudo apt -y upgrade
sudo apt install -y docker docker-compose tmux git pip3 nodejs npm 

# the original docker jonashaag/webfsd works great on amd64, but not on armV7, so I've to build a small modified one
# which supports also older alphine version, as the latest (nighty build) might crash the build (https://stackoverflow.com/a/54003007)
ALPHINE_VERSION=3.10
WEBFS_VERSION=1.21
docker build --network host -t webfs -t webfs:$WEBFS_VERSION --build-arg ALPHINE_VERSION=$ALPHINE_VERSION WEBFS_VERSION=$WEBFS_VERSION docker_webfsd 

# start with
# docker run -it -p9092:80 -v schnipsl-video:/srv webfsd