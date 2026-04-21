import sqlite3
import os
import sys

# CONFIGURATION - Adjust these for staging
DB_PATH = os.environ.get("FLASHARR_DB_PATH", "/app/backend/appData/data/flasharr.db")
DOWNLOADS_DIR = os.environ.get("DOWNLOADS_DIR", "/data/downloads")

def get_missing_list():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all COMPLETED downloads
    cursor.execute("SELECT filename, batch_name, id FROM downloads WHERE state = 'COMPLETED'")
    tasks = cursor.fetchall()
    conn.close()

    missing = []
    for task in tasks:
        filename = task['filename']
        batch_name = task['batch_name']
        
        if batch_name:
            path = os.path.join(DOWNLOADS_DIR, batch_name, filename)
        else:
            path = os.path.join(DOWNLOADS_DIR, filename)
            
        if not os.path.exists(path):
            # Check alternate (no batch)
            if batch_name and os.path.exists(os.path.join(DOWNLOADS_DIR, filename)):
                continue
            missing.append(f"{filename} (Batch: {batch_name or 'None'})")

    print(f"\n--- Found {len(missing)} missing files ---")
    for item in missing:
        print(item)
    
    with open("missing_items.txt", "w") as f:
        f.write("\n".join(missing))
    print(f"\nList saved to missing_items.txt")

if __name__ == "__main__":
    get_missing_list()
