#!/bin/bash

SONARR_URL="http://192.168.1.110:8989"
SONARR_API_KEY="6cc69aeeec80439eadc8ec63ef63f839"
RADARR_URL="http://192.168.1.110:7878"
RADARR_API_KEY="eef7841842cc4a25a75bae282c08db89"

function run_command() {
    local base_url=$1
    local api_key=$2
    local command_name=$3
    
    echo "Triggering $command_name on $base_url..."
    local response=$(curl -s -X POST "$base_url/api/v3/command" \
         -H "X-Api-Key: $api_key" \
         -H "Content-Type: application/json" \
         -d "{\"name\": \"$command_name\"}")
    
    if [[ $response == *"\"id\":"* ]]; then
        echo "  Success: $command_name queued/started."
    else
        echo "  Failed: $response"
    fi
}

echo "Starting Deep Scan for Sonarr & Radarr..."

# Sonarr
run_command "$SONARR_URL" "$SONARR_API_KEY" "RefreshSeries"
run_command "$SONARR_URL" "$SONARR_API_KEY" "RescanSeries"

# Radarr
run_command "$RADARR_URL" "$RADARR_API_KEY" "RefreshMovie"
run_command "$RADARR_URL" "$RADARR_API_KEY" "RescanMovie"

echo "Deep Scan triggers completed."
