#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
# please note that in the actual design ffmpeg might be replaced with a self
# compiled version in the Dockerfile to support the satip:// protocol
#sudo apt install -y ffmpeg
$SUDO apt-get install -y curl
