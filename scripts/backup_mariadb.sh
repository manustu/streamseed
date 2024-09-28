#!/bin/bash

# Define backup directory
BACKUP_DIR="/home/ubuntu/backups/mariadb"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Stop the MariaDB container
docker compose -f /home/ubuntu/streamseed/docker/docker-compose.yml down

# Backup current data
cp -r /home/ubuntu/streamseed/docker/mariadb_data $BACKUP_DIR/mariadb_data_backup_$TIMESTAMP

echo "Backup completed at $BACKUP_DIR/mariadb_data_backup_$TIMESTAMP"
