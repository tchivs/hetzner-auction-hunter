#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Load Settings and Credentials
source ${toolpath}/env.sh

# Decide how to Run
if [[ "${RUN_MODE}" == "container" ]]
then
    # Folder is the Container Folder
    APP_DATA_PATH="${APP_CONTAINER_DATA_PATH}"
    APP_SEARCH_PATH="${APP_CONTAINER_SEARCH_PATH}"
    APP_RESULTS_PATH="${APP_CONTAINER_RESULTS_PATH}"

elif [[ "${RUN_MODE}" == "local" ]]
then
    # Folder is the Host Folder
    APP_DATA_PATH="${APP_HOST_DATA_PATH}"
    APP_SEARCH_PATH="${APP_HOST_SEARCH_PATH}"
    APP_RESULTS_PATH="${APP_HOST_RESULTS_PATH}"
else
    echo "Invalid value for RUN_MODE. Allowed Options are: <local> / <container>"
fi


##################################
######## Store RAW Data ##########
##################################
store_raw_data() {

    # Generate Timestamp
    local ltimestamp=$(date +%Y-%m-%d_%Hh%M)

    # Download and Store the Data in Cache only once, so we don't hit Hetzner Servers too hard
    curl https://www.hetzner.com/_resources/app/jsondata/live_data_sb.json | jq > ${APP_HOST_SEARCH_PATH}/live_data_sb.json

    # Copy file so that we always have a Historic View
    cp ${APP_HOST_SEARCH_PATH}/live_data_sb.json ${APP_HOST_SEARCH_PATH}/${ltimestamp}-live_data_sb.json
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

    # Build list of Arguments for hah.py
    local largs=()
    largs+=("--data-url")
    largs+=("file:///${APP_SEARCH_PATH}/live_data_sb.json")
    largs+=("-f")
    largs+=("${APP_RESULTS_PATH}/${ltimestamp}-${lsearchlabel}.txt")
    largs+=("--provider")
    largs+=("${HAH_PROVIDER}")
    largs+=("--price")
    largs+=("${lprice}")
    largs+=("--exclude-tax")
    largs+=("--ram")
    largs+=("${lram}")
    largs+=("--ecc")
    largs+=("--disk-size")
    largs+=("${ldisk}")
    
    if [[ -n "${lcpusearch}" ]]
    then
        largs+=("--search")
        largs+=("${lcpusearch}")
    fi

    # Decide how to Run
    if [[ "${RUN_MODE}" == "container" ]]
    then
        # Define Container Name
        local lcontainer="hetzner-auction-hunter-${lsearchlabel}"

        # Stop and remove Container if it's currently running
        podman stop --ignore "${lcontainer}"
        podman rm --ignore "${lcontainer}"

        # Run the new Container
        podman run --rm --replace \
        --name="${lcontainer}" \
        -v ${APP_HOST_DATA_PATH}:${APP_CONTAINER_DATA_PATH} \
        -e "NOTIFIERS_PUSHOVER_USER"="${NOTIFIERS_PUSHOVER_USER}" \
        -e "NOTIFIERS_PUSHOVER_TOKEN"="${NOTIFIERS_PUSHOVER_TOKEN}" \
        hetzner-auction-hunter:latest \
        ${largs[*]}
    elif [[ "${RUN_MODE}" == "local" ]]
    then
        # Setup Python venv
        if [[ ! -d "${toolpath}/venv" ]]
        then
            python3  -m venv venv
        fi

        # Activate Python venv
        source "${toolpath}/venv/bin/activate"

        # Install Python venv
        pip install -r "${toolpath}/requirements.txt"
        pip install --upgrade -r "${toolpath}/requirements.txt"

        # Run the APP
        ./hah.py ${largs[*]}
    else
        echo "Invalid value for RUN_MODE. Allowed Options are: <local> / <container>"
    fi
}

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

# Perform all the Searches we need now
perform_search "search-abcde" "80" "128" "960" "1275"

# Perform all the Searches we need now
perform_search "search-fghij" "80" "128" "960" ""



# Unset all Variables that we imported
unset $(grep -v '^#' ${toolpath}/.env | sed -E 's/(.*)=.*/\1/' | xargs)
