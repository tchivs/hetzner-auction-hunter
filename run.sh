#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Set Environment
source "${toolpath}/env.sh"

# Include Functions
source "${toolpath}/functions.sh"

##################################
############## Main ##############
##################################

# Create Folders if not exist yet
# This is Always done on the Host
mkdir -p ${APP_HOST_DATA_PATH}
mkdir -p ${APP_HOST_SEARCH_PATH}
mkdir -p ${APP_HOST_RESULTS_PATH}

# Store RAW Data only Once
store_raw_data

# Perform Searches that the User defined
source "${toolpath}/search.sh"

# Unset all Variables that we imported
unset $(grep -v '^#' ${toolpath}/.env | sed -E 's/(.*)=.*/\1/' | xargs)
