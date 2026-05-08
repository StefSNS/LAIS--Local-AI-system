import sqlite3, os

omnis_db = r'%USERPROFILE%\Desktop\AI projects\Projects\Omnis\knowledge\memory\unified_memory.db'
print("Omnis DB exists:", os.path.exists(omnis_db))

conn = sqlite3.connect(omnis_db)
cur = conn.cursor()

# Get tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Omnis tables:", tables)

# Show schema for each table
for t in tables:
    cur.execute(f"PRAGMA table_info({t[0]})")
    print(f"\n{t[0]} schema:")
    for col in cur.fetchall():
        print(f"  {col}")

# Count existing entries
try:
    cur.execute("SELECT COUNT(*) FROM memory_entries")
    print(f"\nExisting memory entries: {cur.fetchone()[0]}")
    cur.execute("SELECT DISTINCT source FROM memory_entries")
    print("Sources:", cur.fetchall())
except Exception as e:
    print(f"Error: {e}")

conn.close()
