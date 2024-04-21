#!/bin/bash

# Optional argument
engine=${1-"podman"}

# Container Name
name="hetzner-auction-hunter"

# Location of Build Sources
buildfolder="build"

# Target Platform
targetplatform="linux/amd64"

# Repository
# For Remote Pulls
repository="https://github.com/luckylinux/hetzner-auction-hunter"

# For Local Pulls
#repository="./"

# Which CPUs to use during Build
cpus="0,1,2,3"

# Save Current Folder
currentpath=$(pwd)

# Options
# Declare Options Array
opts=()

# Options
# Use --no-cache when e.g. updating docker-entrypoint.sh and images don't get updated as they should
#opts+=("--cpuset-cpus=${cpus}")
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

# Create Folder if not Exist
mkdir -p "${buildfolder}"

# Change Folder
cd ${buildfolder} || exit

# Is this a git Repository already ?
#gitstatus=$(git rev-parse --is-inside-work-tree 2>/dev/null)

# Check if GitHub Repository has already been cloned
#if [[ $gitstatus -ne 0 ]]
#then
#   # This is NOT a git Repository yet
#   # Clone Repository
#   git clone "${repository}.git" .
#else
#   # This may be a git Repository
#   if [[ "${gitstatus}" == "true" ]]
#   then
#       # This is indeed a git Repository
#       # Perform Updates
#       git fetch
#       git merge
#   else
#       # This is not a git Working Tree
#       # Clone
#       git clone "${repository}.git" .
#   fi
#fi

# Copy requirements into the build context
cp -a ../Dockerfile .

# Copy app part from scratch, making sure no old/dangling files are left
rm -rf  ./app/*
mkdir -p app
cp -ar ../app/ .

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
cd ${currentpath} || exit
