import sqlite3
import os
import sys
from pathlib import Path

# =========================================================================
# CONFIGURATION
# =========================================================================
# Adjust these paths based on your Proxmox/LXC setup.
# By default, we use paths common in the Flasharr/Arr LXC environment.

DB_PATH = os.environ.get("FLASHARR_DB_PATH", "/app/backend/appData/data/flasharr.db")
DOWNLOADS_DIR = os.environ.get("DOWNLOADS_DIR", "/data/downloads")
MOVIES_DIR = os.environ.get("MOVIES_DIR", "/data/movies")
TV_DIR = os.environ.get("TV_DIR", "/data/tv")

# =========================================================================

def get_db_connection():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def repair_links():
    print(f"--- Flasharr Link Repair Utility ---")
    print(f"DB: {DB_PATH}")
    print(f"Downloads: {DOWNLOADS_DIR}")
    print(f"Movies: {MOVIES_DIR}")
    print(f"TV: {TV_DIR}")
    print("-" * 40)

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get completed downloads with TMDB metadata
    query = """
    SELECT filename, batch_name, category, tmdb_title, tmdb_season, tmdb_episode, tmdb_id
    FROM downloads 
    WHERE state = 'COMPLETED' AND tmdb_title IS NOT NULL
    """
    
    cursor.execute(query)
    tasks = cursor.fetchall()
    conn.close()

    print(f"Processing {len(tasks)} completed tasks...")
    
    repaired = 0
    skipped = 0
    already_linked = 0

    for task in tasks:
        filename = task['filename']
        batch_name = task['batch_name']
        category = task['category']
        title = task['tmdb_title']
        season = task['tmdb_season']
        
        # Determine Source Path
        # Flasharr stores files in /downloads/ or /downloads/BatchName/
        if batch_name:
            source_path = os.path.join(DOWNLOADS_DIR, batch_name, filename)
        else:
            source_path = os.path.join(DOWNLOADS_DIR, filename)
            
        if not os.path.exists(source_path):
            # Try alternate (no batch) if not found with batch
            if batch_name:
                alt_source = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.exists(alt_source):
                    source_path = alt_source
                else:
                    print(f"Source missing: {filename}")
                    skipped += 1
                    continue
            else:
                print(f"Source missing: {filename}")
                skipped += 1
                continue

        # Determine Target Path
        target_dir = None
        if category == 'movies' or (not category and 'movie' in title.lower()):
            # /data/movies/Title (Year)/Title.ext
            # Note: year is missing in schema, so we just use title
            target_dir = os.path.join(MOVIES_DIR, title)
        elif category == 'tv' or season is not None:
            # /data/tv/Title/Season XX/Title.ext
            season_str = f"Season {int(season):02d}" if season is not None else "Season 01"
            target_dir = os.path.join(TV_DIR, title, season_str)
        else:
            print(f"Skipping {filename}: Unable to determine category (movie/tv)")
            skipped += 1
            continue

        target_path = os.path.join(target_dir, filename)

        # Check if exists
        if os.path.exists(target_path):
            already_linked += 1
            continue

        # Create target dir
        try:
            os.makedirs(target_dir, exist_ok=True)
            os.symlink(source_path, target_path)
            print(f"Linked: {filename} -> {target_path}")
            repaired += 1
        except Exception as e:
            print(f"Error linking {filename}: {e}")
            skipped += 1

    print("-" * 40)
    print(f"Repair Complete!")
    print(f"Repaired: {repaired}")
    print(f"Already Correct: {already_linked}")
    print(f"Skipped/Missing: {skipped}")

if __name__ == "__main__":
    repair_links()
