#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
$SUDO apt-get install -y curl gnupg
curl -sL https://deb.nodesource.com/setup_14.x  | $SUDO bash -
$SUDO apt-get install -y nodejs python3-xmltodict libyajl-dev curl ffmpeg
npm install dvbtee
$SUDO pip3 install jsonslicer xmltodict
