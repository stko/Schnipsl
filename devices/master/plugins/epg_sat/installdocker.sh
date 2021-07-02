#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
apt-get update
apt-get install -y nodejs npm python3-xmltodict libyajl-dev curl ffmpeg
npm install dvbtee
pip install jsonslicer xmltodict