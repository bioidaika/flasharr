import requests
import json
import sys

API_KEY = "6cc69aeeec80439eadc8ec63ef63f839"
BASE_URL = "http://192.168.1.110:8989/api/v3"

def main():
    headers = {"X-Api-Key": API_KEY}
    
    print("Fetching all series...")
    r = requests.get(f"{BASE_URL}/series", headers=headers)
    if r.status_code != 200:
        print(f"Error fetching series: {r.status_code}")
        print(r.text)
        return

    series_list = r.json()
    print(f"Found {len(series_list)} series.")

    for series in series_list:
        series_id = series['id']
        title = series['title']
        print(f"Processing: {title} (ID: {series_id})")
        
        # 1. Update Series & Seasons monitoring
        changed = False
        if not series.get('monitored'):
            series['monitored'] = True
            changed = True
            
        for season in series.get('seasons', []):
            if season['seasonNumber'] == 0:
                if season.get('monitored', True):
                    season['monitored'] = False
                    changed = True
            else:
                if not season.get('monitored'):
                    season['monitored'] = True
                    changed = True
        
        if changed:
            print(f"  Updating series monitoring...")
            up_r = requests.put(f"{BASE_URL}/series/{series_id}", headers=headers, json=series)
            if up_r.status_code not in [200, 202]:
                print(f"    Error updating series: {up_r.status_code}")

        # 2. Update Episodes monitoring
        print(f"  Fetching episodes for {title}...")
        ep_r = requests.get(f"{BASE_URL}/episode", headers=headers, params={"seriesId": series_id})
        if ep_r.status_code == 200:
            episodes = ep_r.json()
            to_monitor = [ep['id'] for ep in episodes if ep['seasonNumber'] > 0 and not ep.get('monitored')]
            to_unmonitor = [ep['id'] for ep in episodes if ep['seasonNumber'] == 0 and ep.get('monitored')]
            
            if to_monitor:
                print(f"    Monitoring {len(to_monitor)} regular episodes...")
                requests.put(f"{BASE_URL}/episode/monitor", headers=headers, json={
                    "episodeIds": to_monitor,
                    "monitored": True
                })
            
            if to_unmonitor:
                print(f"    Unmonitoring {len(to_unmonitor)} special episodes...")
                requests.put(f"{BASE_URL}/episode/monitor", headers=headers, json={
                    "episodeIds": to_unmonitor,
                    "monitored": False
                })
        else:
            print(f"    Error fetching episodes: {ep_r.status_code}")

if __name__ == "__main__":
    main()
