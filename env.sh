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

# Include Functions
source "${toolpath}/functions.sh"

# Load the Environment Variables into THIS Script
#shdoteven --env ".env"
#eval "$(shdotenv --env .env || echo \"exit $?\")"
eval "$(shdotenv --overload --env .env || echo \"exit $?\")"

# Convert Variables to full Paths
APP_HOST_DATA_PATH=$(realpath --canonicalize-missing "${APP_HOST_DATA_PATH}")
APP_HOST_SEARCH_PATH=$(realpath --canonicalize-missing "${APP_HOST_SEARCH_PATH}")
APP_HOST_RESULTS_PATH=$(realpath --canonicalize-missing "${APP_HOST_RESULTS_PATH}")
APP_CONTAINER_DATA_PATH=$(realpath --canonicalize-missing "${APP_CONTAINER_DATA_PATH}")
APP_CONTAINER_SEARCH_PATH=$(realpath --canonicalize-missing "${APP_CONTAINER_SEARCH_PATH}")
APP_CONTAINER_RESULTS_PATH=$(realpath --canonicalize-missing "${APP_CONTAINER_RESULTS_PATH}")

# Autodetect Container Engine if nothing is Specified
if [[ -z "${CONTAINER_ENGINE}" ]]
then
   if [[ -n $(command -v podman) ]]
   then
      # Use Podman if available
      engine="podman"
   elif [[ -n $(command -v docker) ]]
   then
      # Use Docker if available
      engine="docker"
   else
      # Autodetection failed
      echo "ERROR: Could not automatically detect Container Engine. Neither <podman> nor <docker> could be found on the System"
      echo "       Maybe you need to adjust your PATH environment variabke ?"
      echo "ABORTING EXECUTION"
      exit 8
   fi
else
   # Use the value set in the Environment Variable
   engine="${CONTAINER_ENGINE}"
fi

# Check that the speciied Container Engine can be found on the System
if [[ -n $(command -v podman) ]] && [[ "$engine" == "podman" ]]
then
    # OK
    x=1
elif [[ -n $(command -v docker) ]] && [[ "$engine" == "docker" ]]
then
    # OK
    x=1
else
    # Error
    echo "ERROR: Neither <podman> nor <docker> could be found and/or the specified ContainerEngine <${engine}> was not valid."
    echo "       Maybe you need to adjust your PATH environment variabke ?"
    echo "ABORTING EXECUTION"
    exit 7
fi

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
    echo "Invalid value for RUN_MODE. Allowed Options are: <local> / <container>. Got <${RUN_MODE}>."
fi

# Show Running Configuration
if [ -n "${PRINT_CONFIGURATION}" ] && [ "${PRINT_CONFIGURATION}" == "yes" ]
then
	# Build Section
	add_section "#" "1" "Configuration Variables"

	# Print Actual Data
	column -t -s "|" <<-EOF
	Parameter|Value
	Host Data Path|${APP_HOST_DATA_PATH}
	Host Search Path|${APP_HOST_DATA_PATH}
	Host Results Path|${APP_HOST_DATA_PATH}

	Container Data Path|${APP_CONTAINER_DATA_PATH}
	Container Search Path|${APP_CONTAINER_DATA_PATH}
	Container Results Path|${APP_CONTAINER_DATA_PATH}

	Run Mode set to|${RUN_MODE}

	Data Path|${APP_DATA_PATH}
	Search Path|${APP_DATA_PATH}
	Results Path|${APP_DATA_PATH}
	EOF
fi
