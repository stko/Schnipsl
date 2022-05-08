#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
$SUDO apt-get install -y curl gnupg
curl -sL https://deb.nodesource.com/setup_14.x  | $SUDO bash -
# please note that in the actual design ffmpeg might be replaced with a self
# compiled version in the Dockerfile to support the satip:// protocol
#sudo apt install -y ffmpeg
$SUDO apt-get install -y nodejs python3-xmltodict libyajl-dev curl
npm install dvbtee
$SUDO pip3 install jsonslicer xmltodict
