#!/bin/bash
RADARR_URL="http://192.168.1.110:7878"
API_KEY="eef7841842cc4a25a75bae282c08db89"
VALID_ROOT="/data/media/movies"

collections=$(curl -s "${RADARR_URL}/api/v3/collection" -H "X-Api-Key: ${API_KEY}")

echo "$collections" | jq -c '.[]' | while read -r collection; do
    id=$(echo "$collection" | jq '.id')
    title=$(echo "$collection" | jq -r '.title')
    root=$(echo "$collection" | jq -r '.rootFolderPath')
    
    if [ "$root" != "$VALID_ROOT" ]; then
        echo "Fixing collection: $title ($root -> $VALID_ROOT)"
        
        # Update root folder in the json
        updated_collection=$(echo "$collection" | jq --arg path "$VALID_ROOT" '.rootFolderPath = $path')
        
        # PUT back
        curl -s -X PUT "${RADARR_URL}/api/v3/collection/${id}" \
            -H "X-Api-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d "$updated_collection" > /dev/null
    fi
done
echo "Done."
