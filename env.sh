#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Load the Environment Variables into THIS Script
#shdoteven --env ".env"
eval "$(shdotenv --env .env || echo \"exit $?\")"

# Test that it worked
echo "Host Data Path set to: ${APP_HOST_DATA_PATH}"
echo "Container Data Path set to: ${APP_CONTAINER_DATA_PATH}"
