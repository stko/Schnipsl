#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR
#$SUDO apt-get install -y nodejs python3-xmltodict libyajl-dev curl
$SUDO pip3 install requests urllib