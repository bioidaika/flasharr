#!/bin/bash
RADARR_URL="http://192.168.1.110:7878"
API_KEY="eef7841842cc4a25a75bae282c08db89"
VALID_ROOT="/data/media/movies"

# Use the bulk editor if possible, but individual updates are safer if we don't know the bulk schema.
# Actually, the movie editor expects an array of movie IDs to update.
# Let's get the IDs first.
ids=$(curl -s "${RADARR_URL}/api/v3/movie" -H "X-Api-Key: ${API_KEY}" | jq -r '.[] | select(.rootFolderPath != "/data/media/movies") | .id' | tr '\n' ',' | sed 's/,$//')

if [ -z "$ids" ]; then
    echo "No movies to fix."
    exit 0
fi

echo "Fixing movies with IDs: $ids"

# Bulk update root folder
# The JSON for bulk edit is: { "movieIds": [ids], "rootFolderPath": "path", "moveFiles": true }
# Wait, "moveFiles": true might be dangerous if the files are already there or if the source is gone.
# Let's set it to false for now just to fix the DB.
curl -s -X PUT "${RADARR_URL}/api/v3/movie/editor" \
    -H "X-Api-Key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
        \"movieIds\": [${ids}],
        \"rootFolderPath\": \"${VALID_ROOT}\",
        \"moveFiles\": false
    }" > /dev/null

echo "Done."
