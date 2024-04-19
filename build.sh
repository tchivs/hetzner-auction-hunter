#!/bin/bash

# Optional argument
engine=${1-"podman"}

# Container Name
name="hetzner-auction-hunter"

# Location of Sources
subfolder="hetzner-auction-hunter"

# Target Platform
targetplatform="linux/amd64"

# Repository
repository="https://github.com/luckylinux/hetzner-auction-hunter"

# Which CPUs to use during Build
cpus="0,1,2,3"

# Save Current Folder
currentpath=$(pwd)

# Options
# Declare Options Array
opts=()

# Options
# Use --no-cache when e.g. updating docker-entrypoint.sh and images don't get updated as they should
opts+=("--cpuset-cpus=${cpus}")
#opts="--no-cache"

# Mandatory Tag
#tag=$(cat ./tag.txt)
tag=$(date +%Y%m%d)

# Select Dockerfile
buildfile="Dockerfile"

# Check if they are set
if [[ ! -v name ]] || [[ ! -v tag ]]
then
   echo "Both Container Name and Tag Must be Set" !
fi

# Check if GitHub Repository has already been cloned
if [[ ! -d "${subfolder}" ]]
then
   # Clone Repository
   git clone "${repository}.git" "${subfolder}"
fi

# Change Folder
cd ${subfolder}

# Update Local Copy if needed
git pull

# Start with a fresh Dockerfile
wget https://raw.githubusercontent.com/maxroll-media-group/hetzner-auction-hunter/master/Dockerfile -O ${buildfile}

# Replace Python Version in Dockerfile
sed -Ei "s|FROM python:3.10-slim-buster(.*?)$|FROM python:3.11-slim-bookworm\1|g" ${buildfile}

# Also enable Python while we are at it
#sed -Ei "s|.*?(RUN apk update)$|\1\nRUN apk add --no-cache python3 py3-pip python3-dev pixman-dev cairo cairo-dev pango pango-dev make g++|g" ${buildfile}
#cat ${buildfile}

# Copy requirements into the build context
# cp <myfolder> . -r docker build . -t  project:latest

# Prefer Podman over Docker
if [[ -n $(command -v podman) ]] && [[ "$engine" == "podman" ]]
then
    # Use Podman and ./build/ folder to build the image
    podman build ${opts[*]} -f $buildfile . -t ${name,,}:$tag -t ${name,,}:latest
elif [[ -n $(command -v docker) ]] && [[ "$engine" == "docker" ]]
then
    # Use Docker and ./build/ folder to build the image
    docker build ${opts[*]} -f $buildfile . -t ${name,,}:$tag -t ${name,,}:latest
else
    # Error
    echo "Neither Podman nor Docker could be found and/or the specified Engine <$engine> was not valid. Aborting !"
fi

# Change Back to Current Path
cd ${currentpath}
