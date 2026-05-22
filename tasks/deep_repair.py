import sqlite3
import os
import subprocess
import json
import re

DB_PATH = "/mnt/appdata/flasharr/data/flasharr.db"
# Hosts perspective (LXC 110/112)
TV_ROOT = "/data/media/tv"
DOWNLOAD_ROOT = "/data/flasharr-download"

# Sonarr API info for lookup
SONARR_URL = "http://192.168.1.110:8989"
SONARR_API_KEY = "6cc69aeeec80439eadc8ec63ef63f839"

def run_sql(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def update_sql(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount

def check_file(path):
    actual_path = path
    if path.startswith("/appData/downloads/"):
        actual_path = path.replace("/appData/downloads/", f"{DOWNLOAD_ROOT}/")
    elif path.startswith("/downloads/"):
        actual_path = path.replace("/downloads/", f"{DOWNLOAD_ROOT}/")
    
    return os.path.exists(actual_path), actual_path

def fix_metadata():
    print("--- Fixing Metadata ---")
    
    # 1. One Piece: Live Action (111110) vs Anime (37854)
    items = run_sql("SELECT id, filename, tmdb_id FROM downloads WHERE filename LIKE '%ONE PIECE%'")
    for row_id, filename, tmdb_id in items:
        # If it has S02... or episode numbers > 8 (LA has 8 eps), it's Anime
        is_anime = False
        if "S02" in filename or "S03" in filename or "S04" in filename:
            is_anime = True
        
        # Check episode number if S01
        if "S01E" in filename:
            match = re.search(r'S01E(\d+)', filename)
            if match and int(match.group(1)) > 8:
                is_anime = True

        if is_anime and tmdb_id == 111110:
            print(f"Correcting {filename}: Live Action -> Anime (37854)")
            update_sql("UPDATE downloads SET tmdb_id = 37854 WHERE id = ?", (row_id,))
        elif not is_anime and tmdb_id == 37854:
            print(f"Correcting {filename}: Anime -> Live Action (111110)")
            update_sql("UPDATE downloads SET tmdb_id = 111110 WHERE id = ?", (row_id,))

def repair_paths():
    print("--- Repairing Paths and Symlinks ---")
    items = run_sql("SELECT id, filename, destination, tmdb_id, tmdb_season FROM downloads WHERE state = 'COMPLETED'")
    
    for row_id, filename, destination, tmdb_id, season in items:
        if not destination: continue
        
        # 1. Normalize path strings
        new_dest = destination
        if new_dest.startswith("/downloads/"):
            new_dest = new_dest.replace("/downloads/", "/appData/downloads/")
        
        # Season normalization (Season 01 -> Season 1)
        if "Season 0" in new_dest:
            new_dest = re.sub(r'Season 0(\d)', r'Season \1', new_dest)
            
        if new_dest != destination:
            print(f"Updating DB path for {filename}: {destination} -> {new_dest}")
            update_sql("UPDATE downloads SET destination = ? WHERE id = ?", (new_dest, row_id))
            destination = new_dest

        # 2. Check existence and fix Missing items
        exists, actual_path = check_file(destination)
        
        if not exists:
            # Maybe it moved to the library already?
            # Try to build the expected library path
            # Series: /data/media/tv/Series Name/Season X/filename
            
            # For simplicity, let's look for the filename in the whole TV root
            # This is slow but thorough for a one-time fix
            find_cmd = f"find {TV_ROOT} -name \"{filename}\" -print -quit"
            try:
                found_path = subprocess.check_output(find_cmd, shell=True).decode().strip()
                if found_path:
                    print(f"  Found {filename} in library: {found_path}")
                    update_sql("UPDATE downloads SET destination = ? WHERE id = ?", (found_path, row_id))
                    continue
            except:
                pass
            
            print(f"  Still MISSING: {filename}")

def trigger_rescans():
    print("--- Triggering Sonarr Rescans ---")
    # Get all unique series IDs we have downloads for
    series_ids = [r[0] for r in run_sql("SELECT DISTINCT tmdb_id FROM downloads WHERE tmdb_id IS NOT NULL")]
    for tid in series_ids:
        # We need Sonarr internal ID, not TMDB ID.
        # For now, let's just trigger the ones we know are problematic.
        pass
    
    # Trigger One Piece (2023) and Tales of Herding Gods
    for sid in [66, 62]:
        print(f"Triggering Sonarr rescan for series {sid}")
        subprocess.run(["curl", "-s", "-X", "POST", "-H", f"X-Api-Key: {SONARR_API_KEY}", "-d", f'{{"name": "RescanSeries", "seriesId": {sid}}}', f"{SONARR_URL}/api/v3/command"])

if __name__ == "__main__":
    fix_metadata()
    repair_paths()
    trigger_rescans()
