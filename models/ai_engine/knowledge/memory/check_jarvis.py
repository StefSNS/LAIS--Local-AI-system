import os
import sqlite3

jarvis_db = os.environ.get("JARVIS_MEMORY_DB", r'%USERPROFILE%\Desktop\AI projects\Mark-XXXV\memory\jarvis_memory.db')
conn = sqlite3.connect(jarvis_db)
cur = conn.cursor()

# Get tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Jarvis tables:", tables)

# Get unique entries
cur.execute("SELECT DISTINCT category, key, value FROM memory_entries")
unique_rows = cur.fetchall()
print("\nUnique memory entries:")
for r in unique_rows:
    print(f"  {r[0]}/{r[1]}: {r[2][:80]}")

# Count duplicates
cur.execute("SELECT category, key, COUNT(*) FROM memory_entries GROUP BY category, key")
print("\nEntry counts per key:")
for r in cur.fetchall():
    print(f"  {r[0]}/{r[1]}: {r[2]} rows")

# Total rows
cur.execute("SELECT COUNT(*) FROM memory_entries")
print(f"\nTotal memory rows (with duplicates): {cur.fetchone()[0]}")

# Check for conversations table
try:
    cur.execute("SELECT COUNT(*) FROM conversations")
    print(f"Conversations: {cur.fetchone()[0]}")
except Exception as e:
    print("No conversations table found")

conn.close()
