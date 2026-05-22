import requests
import sys

SONARR_URL = "http://192.168.1.110:8989"
SONARR_API_KEY = "6cc69aeeec80439eadc8ec63ef63f839"
RADARR_URL = "http://192.168.1.110:7878"
RADARR_API_KEY = "eef7841842cc4a25a75bae282c08db89"

def run_command(base_url, api_key, command_name):
    print(f"Triggering {command_name} on {base_url}...")
    url = f"{base_url}/api/v3/command"
    headers = {"X-Api-Key": api_key}
    payload = {"name": command_name}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [201, 202, 200]:
            print(f"  Success: {command_name} queued.")
        else:
            print(f"  Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  Failed to connect: {e}")

def deep_scan():
    # Sonarr: Refresh all series and then trigger a rescan
    # Note: 'RefreshSeries' refreshes metadata, 'RescanSeries' scans the disk
    run_command(SONARR_URL, SONARR_API_KEY, "RefreshSeries")
    run_command(SONARR_URL, SONARR_API_KEY, "RescanSeries") # For Sonarr, this is often 'RescanSeries'
    
    # Radarr: Refresh all movies
    run_command(RADARR_URL, RADARR_API_KEY, "RefreshMovie")
    # For Radarr, RefreshMovie usually includes a disk scan if configured, 
    # but we can also trigger 'RescanMovie' if supported in v3
    run_command(RADARR_URL, RADARR_API_KEY, "RescanMovie")

if __name__ == "__main__":
    deep_scan()
