#!/bin/bash

# This file can only be sources
# It CANNOT be directly executed !
if [ ${0##*/} == ${BASH_SOURCE[0]##*/} ]; then
    echo "WARNING"
    echo "This script is not meant to be executed directly!"
    echo "Use this script only by sourcing it."
    echo -e "\n"
    exit 1
fi

##################################
####### Helper Functions #########
##################################

# Repeat Character N times
repeat_character() {
   # Character to repeat
   local lcharacter=${1}

   # Number of Repetitions
   local lrepetitions=${2}

   # Print using Brace Expansion
   #for i in {1 ... ${lrepetitions}}
   for i in $(seq 1 1 ${lrepetitions})
   do
       echo -n "${lcharacter}"
   done
}

# Add Line Separator
add_separator() {
   local lcharacter=${1-"#"}
   local lrows=${2-"1"}

   # Get width of Terminal
   local lwidth=$(tput cols)

   # Repeat Character
   for r in $(seq 1 1 ${lrows})
   do
      repeat_character "${lcharacter}" "${lwidth}"
   done
}

# Add Line Separator with Description
add_section() {
   local lcharacter=${1-"#"}
   local lrows=${2-"1"}
   local ldescription=${3-""}

   # Determine number of Separators BEFORE and AFTER the Description
   #local lrowsseparatorsbefore=$(echo "${lrows-1} / ( 2 )" | bc -l)
   #local lrowsseparatorafter="${lrowsseparatorsbefore}"
   local lrowsbefore="${lrows}"
   local lrowsafter="${lrows}"

   # Add Separator
   add_separator "${lcharacter}" "${lrowsbefore}"

   # Add Header with Description
   add_description "${lcharacter}" "${ldescription}"

   # Add Separator
   add_separator "${lcharacter}" "${lrowsafter}"
}

add_description() {
   # User Inputs
   local lcharacter=${1-"#"}
   local ldescription=${2-""}

   # Add one Space before and after the original String
   ldescription=" ${ldescription} "

   # Get width of Terminal
   local lwidth=$(tput cols)

   # Get length of Description
   local llengthdescription=${#ldescription}

   # Get width of Terminal
   local lwidth=$(tput cols)

   # Subtract Description from Terminal Width
   local llengthseparator=$((lwidth - llengthdescription))

   # Divide by two
   local llengtheachseparator=$(echo "${llengthseparator} / ( 2 )" | bc -l)

   # Remainer
   local lremainer=$((llengthseparator % 2))
   local lextrastr=$(repeat_character "${lcharacter}" "${lremainer}")

   # Get String of Characters for BEFORE and AFTER the Description
   local lseparator=$(repeat_character "${lcharacter}" "${llengtheachseparator}")

   # Print Description Line
   echo "${lseparator}${ldescription}${lextrastr}${lseparator}"
}


##################################
######## Store RAW Data ##########
##################################
store_raw_data() {
    # Build Section
    if [ -n "${PRINT_CONFIGURATION}" ] && [ "${PRINT_CONFIGURATION}" == "yes" ]
    then
       add_section "#" "1" "Caching Hetzner Server List"
    fi

    # Generate Timestamp
    local ltimestamp=$(date +%Y-%m-%d_%Hh%M)

    # Download and Store the Data in Cache only once, so we don't hit Hetzner Servers too hard
    curl -s https://www.hetzner.com/_resources/app/jsondata/live_data_sb.json | jq > ${APP_HOST_SEARCH_PATH}/live_data_sb.json

    # Copy file so that we always have a Historic View
    cp ${APP_HOST_SEARCH_PATH}/live_data_sb.json ${APP_HOST_SEARCH_PATH}/${ltimestamp}-live_data_sb.json
}

##################################
######## Perform Search ##########
##################################
perform_search() {
    # Build Section
    if [ -n "${PRINT_CONFIGURATION}" ] && [ "${PRINT_CONFIGURATION}" == "yes" ]
    then
       add_section "#" "1" "Performing Server Search"
    fi

    local lsearchlabel="$1"
    local lsearchcriteria="${@:2}"
    #local lprice="$2"
    #local lram="$3"
    #local ldisk="$4"
    #local lcpusearch="$5"
    echo "Search Arguments: ${lsearchcriteria[*]}"

    # The Argument List is passed by nameref
    #declare -n lhahargsref="${1}" # Reference to output array

    # Generate Timestamp
    local ltimestamp=$(date +%Y-%m-%d_%Hh%M)

    # Build list of Arguments for hah.py
    local lhahargs=()
    lhahargs+=("--data-url")
    lhahargs+=("file:///${APP_SEARCH_PATH}/live_data_sb.json")
    lhahargs+=("-f")
    lhahargs+=("${APP_RESULTS_PATH}/${ltimestamp}-${lsearchlabel}.txt")
    lhahargs+=("--provider")
    lhahargs+=("${HAH_PROVIDER}")
    for larg in "${lsearchcriteria}"
    do
        lhahargs+=("$larg")
    done
    #lhahargs+=$lsearchcriteria
    #lhahargs+=("--price")
    #lhahargs+=("${lprice}")
    #lhahargs+=("--exclude-tax")
    #lhahargs+=("--ram")
    #lhahargs+=("${lram}")
    #lhahargs+=("--ecc")
    #lhahargs+=("--disk-size")
    #lhahargs+=("${ldisk}")

    # If CPU search is set then include it
    #if [[ -n "${lcpusearch}" ]]
    #then
    #    lhahargs+=("--match-cpu")
    #    lhahargs+=("${lcpusearch}")
    #fi

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
        ${lhahargs[*]}
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
        pip install -q -r "${toolpath}/app/requirements.txt"

        # Automatically Upgrade Python venv
        pip install -q --upgrade -r "${toolpath}/app/requirements.txt"

        # Run the APP
        ./app/hah.py ${lhahargs[*]}
    else
        echo "Invalid value for RUN_MODE. Allowed Options are: <local> / <container>. Got <${RUN_MODE}>."
    fi
}
