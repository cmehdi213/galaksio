#!/bin/bash
set -e

# Galaksio Startup Script
# This script starts the Galaksio application with Apache

echo "Starting Galaksio 2 - Modern Galaxy Workflow Interface..."

# Wait for dependent services (if any)
if [ "$WAIT_FOR_REDIS" = "true" ]; then
    echo "Waiting for Redis..."
    while ! nc -z redis 6379; do
        sleep 1
    done
    echo "Redis is ready!"
fi

if [ "$WAIT_FOR_POSTGRES" = "true" ]; then
    echo "Waiting for PostgreSQL..."
    while ! nc -z postgres 5432; do
        sleep 1
    done
    echo "PostgreSQL is ready!"
fi

# Initialize configuration if not exists
if [ ! -f "/app/server/conf/serverconf.cfg" ]; then
    echo "Initializing default configuration..."
    cp /app/server/resources/example_serverconf.cfg /app/server/conf/serverconf.cfg
    chown galaksio:galaksio /app/server/conf/serverconf.cfg
fi

# Set proper permissions
chown -R galaksio:galaksio /app/server/conf /app/server/log

# Start Apache
echo "Starting Apache server..."
apache2ctl -D FOREGROUND
