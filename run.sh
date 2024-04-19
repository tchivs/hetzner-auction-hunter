#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Setup Python venv
if [[ ! -d "${toolpath}/venv" ]]
then
    python3  -m venv venv
fi

# Activate Python venv
source "${toolpath}/venv/bin/activate"

# Install Python venv
pip install -r "${toolpath}/requirements.txt"
pip install --update -r "${toolpath}/requirements.txt"

# Load Settings and Credentials
#export $(grep -v '^#' ${toolpath}/.env | xargs -d '\n')
#source ${toolpath}/.env
set -a
. ${toolpath}/.env
set +a

# Data Folder
datafolder="${HOME}/containers/data/hetzner-auction-hunter"

# Search Folder
searchfolder="${datafolder}/search"

# Results Folder
resultsfolder="${datafolder}/results"

##################################
######## Store RAW Data ##########
##################################
store_raw_data() {

# Generate Timestamp
local ltimestamp=$(date +%Y-%m-%d_%Hh%M)

# Download and Store the Data in Cache only once, so we don't hit Hetzner Servers too hard
curl https://www.hetzner.com/_resources/app/jsondata/live_data_sb.json | jq > ${searchfolder}/live_data_sb.json

# Copy file so that we always have a Historic View
cp ${searchfolder}/live_data_sb.json ${searchfolder}/${ltimestamp}-live_data_sb.json
}

##################################
######## Perform Search ##########
##################################
perform_search() {
 local lsearchlabel="$1"
 local lprice="$2"
 local lram="$3"
 local ldisk="$4"
 local lcpusearch="$5"

 # Generate Timestamp
 local ltimestamp=$(date +%Y-%m-%d_%Hh%M)

 # Define Container Name
 local lcontainer="hetzner-auction-hunter-${lsearchlabel}"

 # Stop and remove Container if it's currently running
 podman stop --ignore "${lcontainer}"
 podman rm --ignore "${lcontainer}"

 # Run the new Container
 podman run --rm --replace \
 --name="${lcontainer}" \
 -v :/data \
 -e "NOTIFIERS_PUSHOVER_USER"="${NOTIFIERS_PUSHOVER_USER}" \
 -e "NOTIFIERS_PUSHOVER_TOKEN"="${NOTIFIERS_PUSHOVER_TOKEN}" \
 hetzner-auction-hunter:latest \
 --data-url "file:////data/search/live_data_sb.json" \
 -f "/data/results/${ltimestamp}-${lsearchlabel}.txt" \
 --provider "${HAH_PROVIDER}" \
 --price "${lprice}" \
 --ram "${lram}" \
 --ecc \
 --disk-size "${ldisk}" \
 --search "${lcpusearch}"
}

##################################
############## Main ##############
##################################


# Create Folders if not exist yet
mkdir -p ${datafolder}
mkdir -p ${searchfolder}
mkdir -p ${resultsfolder}

# Store RAW Data only Once
store_raw_data

# Perform all the Searches we need now
perform_search "search-abcde" "50" "64" "960" "1275"

# Perform all the Searches we need now
perform_search "search-fghij" "50" "64" "960" ""



# Unset all Variables that we imported
unset $(grep -v '^#' ${toolpath}/.env | sed -E 's/(.*)=.*/\1/' | xargs)
