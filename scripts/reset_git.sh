#!/bin/bash

# Get the hostname
HOSTNAME=$(hostname)

# Check the hostname and change directory accordingly
if [ "$HOSTNAME" = "live-server" ]; then
    cd /home/ubuntu/streamseed
elif [ "$HOSTNAME" = "development-server" ]; then
    cd /home/sramsay/streamseed
else
    echo "Hostname not recognized. Exiting."
    exit 1
fi

# Reset local changes
git reset --hard HEAD

# Pull the latest changes from the repository
git pull
