
import requests
import json

RADARR_URL = "http://192.168.1.110:7878"
API_KEY = "eef7841842cc4a25a75bae282c08db89"
VALID_ROOT = "/data/media/movies"

def fix_collections():
    # Get all collections
    response = requests.get(f"{RADARR_URL}/api/v3/collection", headers={"X-Api-Key": API_KEY})
    collections = response.json()
    
    updated_count = 0
    for collection in collections:
        if collection.get("rootFolderPath") != VALID_ROOT:
            print(f"Fixing collection: {collection['title']} ({collection['rootFolderPath']} -> {VALID_ROOT})")
            collection["rootFolderPath"] = VALID_ROOT
            
            # PUT back
            put_response = requests.put(
                f"{RADARR_URL}/api/v3/collection/{collection['id']}", 
                headers={"X-Api-Key": API_KEY},
                json=collection
            )
            if put_response.status_code in [200, 202]:
                updated_count += 1
            else:
                print(f"  Failed! {put_response.status_code}: {put_response.text}")
                
    print(f"Finished. Updated {updated_count} collections.")

if __name__ == "__main__":
    fix_collections()
