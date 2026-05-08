import sqlite3
import os

from datetime import datetime

# Can override paths via environment variables
JARVIS_DB = os.environ.get("JARVIS_MEMORY_DB", r'%USERPROFILE%\Desktop\AI projects\Mark-XXXV\memory\jarvis_memory.db')
OMNIS_DB = os.environ.get("OMNIS_MEMORY_DB", r'%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\memory\unified_memory.db')

def get_timestamp():
    return datetime.utcnow().isoformat()

def migrate():
    jarvis_conn = sqlite3.connect(JARVIS_DB)
    jarvis_cur = jarvis_conn.cursor()

    omnis_conn = sqlite3.connect(OMNIS_DB)
    omnis_cur = omnis_conn.cursor()

    stats = {
        'jarvis_before_total': 0,
        'jarvis_unique': 0,
        'already_existed': 0,
        'migrated': 0,
        'omnis_before': 0,
        'omnis_after': 0,
        'duplicates_removed': 0
    }

    # Count Omnis entries before
    omnis_cur.execute("SELECT COUNT(*) FROM memory_entries")
    stats['omnis_before'] = omnis_cur.fetchone()[0]

    # Count Jarvis entries before
    jarvis_cur.execute("SELECT COUNT(*) FROM memory_entries")
    stats['jarvis_before_total'] = jarvis_cur.fetchone()[0]

    # Get unique entries from Jarvis
    jarvis_cur.execute("SELECT DISTINCT category, key, value FROM memory_entries")
    unique_entries = jarvis_cur.fetchall()
    stats['jarvis_unique'] = len(unique_entries)

    print(f"Jarvis DB: {stats['jarvis_before_total']} total rows, {stats['jarvis_unique']} unique entries")
    print(f"Omnis DB: {stats['omnis_before']} entries before migration\n")

    # Migrate each unique entry
    for category, key, value in unique_entries:
        # Check if entry already exists in Omnis (by agent + category + key)
        omnis_cur.execute(
            "SELECT COUNT(*) FROM memory_entries WHERE agent='jarvis' AND category=? AND key=?",
            (category, key)
        )
        if omnis_cur.fetchone()[0] > 0:
            print(f"  SKIP (exists): {category}/{key}")
            stats['already_existed'] += 1
            continue

        # Insert into Omnis
        timestamp = get_timestamp()
        omnis_cur.execute(
            "INSERT INTO memory_entries (agent, key, value, category, created, updated) VALUES (?, ?, ?, ?, ?, ?)",
            ('jarvis', key, value, category, timestamp, timestamp)
        )
        print(f"  MIGRATED: {category}/{key}")
        stats['migrated'] += 1

    # Commit Omnis changes
    omnis_conn.commit()

    # Count Omnis entries after
    omnis_cur.execute("SELECT COUNT(*) FROM memory_entries")
    stats['omnis_after'] = omnis_cur.fetchone()[0]

    # Clean up duplicates in Jarvis DB (keep only one row per category+key)
    jarvis_cur.execute("SELECT category, key FROM memory_entries GROUP BY category, key")
    unique_keys = jarvis_cur.fetchall()

    for category, key in unique_keys:
        # Find the id of the first row for this category+key
        jarvis_cur.execute(
            "SELECT id FROM memory_entries WHERE category=? AND key=? ORDER BY id LIMIT 1",
            (category, key)
        )
        keep_id = jarvis_cur.fetchone()[0]

        # Delete all other rows for this category+key
        jarvis_cur.execute(
            "DELETE FROM memory_entries WHERE category=? AND key=? AND id!=?",
            (category, key, keep_id)
        )
        deleted = jarvis_cur.rowcount
        stats['duplicates_removed'] += deleted
        if deleted > 0:
            print(f"  Cleaned {deleted} duplicates for {category}/{key}")

    jarvis_conn.commit()

    # Final counts
    jarvis_cur.execute("SELECT COUNT(*) FROM memory_entries")
    jarvis_after = jarvis_cur.fetchone()[0]

    print(f"\n" + "="*50)
    print("MIGRATION COMPLETE")
    print("="*50)
    print(f"Jarvis DB: {stats['jarvis_before_total']} -> {jarvis_after} rows (removed {stats['duplicates_removed']} duplicates)")
    print(f"Omnis DB: {stats['omnis_before']} -> {stats['omnis_after']} entries")
    print(f"  - Migrated: {stats['migrated']} new entries")
    print(f"  - Already existed: {stats['already_existed']} entries")
    print(f"  - Net new in Omnis: {stats['omnis_after'] - stats['omnis_before']}")

    jarvis_conn.close()
    omnis_conn.close()

    return stats

if __name__ == '__main__':
    migrate()
