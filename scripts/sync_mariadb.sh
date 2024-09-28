#!/bin/bash

# Define variables
LOCAL_DATA_DIR="/home/sramsay/streamseed/docker/mariadb_data"
REMOTE_DATA_DIR="/home/ubuntu/streamseed/docker/mariadb_data"
REMOTE_COMPOSE_FILE="/home/ubuntu/streamseed/docker/docker-compose.yml"
SSH_KEY="/home/sramsay/streamseed/StreamSeedKey.pem"
REMOTE_USER="ubuntu"
REMOTE_HOST="18.130.243.125"

# Stop the MariaDB container on the VPS
ssh -i $SSH_KEY $REMOTE_USER@$REMOTE_HOST "docker-compose -f $REMOTE_COMPOSE_FILE down"

# Use rsync to sync the MariaDB data directory to the VPS
rsync -avz -e "ssh -i $SSH_KEY" $LOCAL_DATA_DIR/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DATA_DIR

# Copy the docker-compose.yml file to the VPS
scp -i $SSH_KEY /home/sramsay/streamseed/docker/docker-compose.yml $REMOTE_USER@$REMOTE_HOST:$REMOTE_COMPOSE_FILE

# Start the MariaDB container on the VPS
ssh -i $SSH_KEY $REMOTE_USER@$REMOTE_HOST "docker compose -f $REMOTE_COMPOSE_FILE up -d"

echo "Sync completed successfully."
