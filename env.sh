#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Load Settings and Credentials
#for item in $(grep -v '^#' ${toolpath}/.env | xargs -d ' '); do v=$(eval $item); export v; done
#for item in $(grep -v '^#' ${toolpath}/.env | xargs -d ' '); do export "$item"; done

#source ${toolpath}/.env
set -a
source "${toolpath}/.env"
set +a

# Test that it worked
echo "Host Data Path set to: ${APP_HOST_DATA_PATH}"
echo "Container Data Path set to: ${APP_CONTAINER_DATA_PATH}"