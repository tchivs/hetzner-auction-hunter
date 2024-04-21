#!/bin/bash

# This is a "Hack" to allow compose.yml to pick up the Latest Image

# Image Name
image=${1-""}
if [[ -z "$image" ]]
then
    read -p "Enter the desired Image Name & Tag to Push to Local Registry: " image
fi

##################################################################################
# Also add entry in the main Regitries Configuration pointing to localhost:5000  #
# e.g. ~/.config/containers/registries.conf                                      #
#  unqualified-search-registries = ["localhost:5000", ...]                       #
##################################################################################

# Automatic Configuration is currently NOT working !!!
#sed -Ei "|^#?\s*?unqualified-search-registries\s*?=\s*?\[\"localhost:5000\"|!s|(.*)|unqualified-search-registries\s*?=\s*?\[\"localhost:5000\" , \1|g" "~/.config/containers/registries.conf"
#sed -Ei '/^##Input/! s/foo/bar/g' myfile

# Create a file /etc/containers/registries.conf.d/local-development.conf
mkdir -p ~/.config/containers/registries.conf.d/
cat > ~/.config/containers/registries.conf.d/local-development.conf <<EOF
[[registry]]
prefix = "localhost:5000"
location = "localhost:5000"
insecure = true
EOF

# Run a Local Registry WITHOUT Persistent Data Storage
podman run -d --replace -p 5000:5000 --name registry registry:2

# Tag the Image
podman tag $image localhost:5000/local/$image

# Push the locally built Image to the Local Registry
podman push --tls-verify=false localhost:5000/local/$image

# Edit docker-compose file to use localhost:5000/local/$image
# ...
