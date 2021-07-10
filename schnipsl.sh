#!/bin/bash

function check_dependencies {
	if ! [ -x "$(command -v docker-compose)" ]; then
		echo '⚠️  Error: docker-compose is not installed.' >&2
		exit 1
	fi

	if ! [ -x "$(command -v git)" ]; then
		echo '⚠️  Error: git is not installed.' >&2
		exit 1
	fi
}

function start {

	echo '🏃 Starting the containers'
	docker-compose up -d $container
}

function stop {
	echo '🛑 Stopping all containers'
	docker-compose stop
}

function teststop {
	echo '🛑 Stopping the schnipsl container '
	containerid=$(docker ps -q --filter "name=schnipsl")
	if [[  -z "containerid" ]]
	then
		echo "⚠️ No running Schnipsl container found"
		exit 1
	fi
	docker stop schnipsl
	if [ ! $? -eq 0 ]; then
		echo '⚠️  Could not stop the Schnipsl container'
	fi

	docker rmi $containerid
	if [ ! $? -eq 0 ]; then
		echo '⚠️  Could not remove t'
	fi
}

function teststop {
	echo '🛑 Stopping the schnipsl container '

	docker stop schnipsl
	if [ ! $? -eq 0 ]; then
		echo '⚠️  Could not stop the Schnipsl container'
	fi

}


function testbuild {
	teststop
	echo '🛑 rebuild  the schnipsl container '
	echo 'Search the schnipsl container '
	containerid=$(docker ps -qa --filter "name=schnipsl")
	if [[  -z "$containerid" ]]
	then
		echo "⚠️ No Schnipsl container found"
	else
		echo "remove the image"
		docker rmi $containerid
		if [ ! $? -eq 0 ]; then
			echo '⚠️  Could not remove the Schnipsl image'
		fi
	fi
	echo "Build the image"
	docker -D build  -t schnipsl .
	if [ ! $? -eq 0 ]; then
		echo '⚠️  Could not build the Schnipsl image'
	fi

}

function teststart {
	containerid=$(docker ps -qa --filter "name=schnipsl")
	if [[  -z "$containerid" ]]
	then
		echo "⚠️ No Schnipsl container found, so create one"
		docker run -i \
		--name schnipsl \
		-v schnipsl-backup:/app/devices/master/volumes/backup \
		-v schnipsl-runtime:/app/devices/master/volumes/runtime \
		-v schnipsl-video:/app/devices/master/volumes/videos/record_hd \
		--network=host \
		schnipsl
	else
		echo "start existing container"
		docker start  -i schnipsl
	fi
}



function fullbackup  {
	if [[  -z "$1" || !  -d "$1" ]]
	then
		echo "⚠️ no or invalid target directory given!: $1"
	else
		echo "start backup: copy .../volumes to $1"
		docker cp schnipsl:/app/devices/master/volumes "$1"
	fi
}



function fullrestore  {
	if [[  -z "$1" || !  -d "$1" ]]
	then
		echo "⚠️ no or invalid target directory given!: $1"
	else
		echo "start backup: copy  $1 to .../volumes"
		docker cp "$1" schnipsl:/app/devices/master/volumes
	fi
}


function backup  {
	if [[  -z "$1" || !  -d "$1" ]]
	then
		echo "⚠️ no or invalid target directory given!: $1"
	else
		echo "start backup: copy .../volumes/backup to $1/backup"
		docker cp schnipsl:/app/devices/master/volumes/backup "$1/backup"
	fi
}



function restore  {
	if [[  -z "$1" || !  -d "$1" ]]
	then
		echo "⚠️ no or invalid target directory given!: $1"
	else
		echo "start backup: copy  $1/backup to .../volumes/backup"
		docker cp "$1/backup" schnipsl:/app/devices/master/volumes/backup
	fi
}



function update {

	if [[ ! -d ".git" ]]
	then
		echo "🛑You have manually downloaded the version of Schnipsl.
The automatic update only works with a cloned Git repository.
Try backing up your settings shutting down all containers with 

docker-compose down --remove orphans

Then copy the current version from GitHub to this folder and run

./schnipsl.sh start.

Alternatively create a Git clone of the repository."
		exit 1
	fi
	echo '☠️  Shutting down all running containers and removing them.'
	docker-compose down --remove-orphans
	if [ ! $? -eq 0 ]; then
		echo '⚠️  Updating failed. Please check the repository on GitHub.'
	fi	    
	echo '⬇️  Pulling latest release via git.'
	git fetch --tags
	latestTag=$(git describe --tags `git rev-list --tags --max-count=1`)
	git checkout $latestTag
	if [ ! $? -eq 0 ]; then
		echo '⚠️  Updating failed. Please check the repository on GitHub.'
	fi	    
	echo '⬇️  Pulling docker images.'
	docker-compose pull
	if [ ! $? -eq 0 ]; then
		echo '⚠️  Updating failed. Please check the repository on GitHub.'
	fi	    
	start
}

check_dependencies

case "$1" in
	"start")
		start
		;;
	"stop")
		stop
		;;
	"update")
		update
		;;
	"data")
		build_data_structure
		;;
	"testbuild")
		testbuild
		;;
	"teststart")
		teststart
		;;
	"teststop")
		teststop
		;;
	"fullbackup")
		fullbackup $2
		;;
	"fullrestore")
		fullrestore  $2
		;;
	"backup")
		backup  $2
		;;
	"restore")
		restore  $2
		;;
	* )
		cat << EOF
📺 Schnipsl – setup script
—————————————————————————————
Usage:
schnipsl.sh update – update to the latest release version
schnipsl.sh start – run all containers
schnipsl.sh stop – stop all containers
schnipsl.sh backup targetdir – backups all config data into targetdir/backup
schnipsl.sh restore sourcedir – restore all config data from targetdir/backup
schnipsl.sh fullbackup targetdir – backups all data, also runtime data and videos, into targetdir
schnipsl.sh fullrestore sourcedir– – restores all data, also runtime data and videos, from targetdir

Check https://github.com/stko/schnipsl/ for updates.
EOF
		;;
esac
