#!/bin/sh
export SUDO=$(which sudo)
$SUDO apt-get update
find -name installdocker.sh -exec chmod a+x {} \; -exec bash -c {}  \;

