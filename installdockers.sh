#!/bin/sh
sudo apt-get update
find -name installdocker.sh -exec chmod a+x {} \; -exec bash -c {}  \;

