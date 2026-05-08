import sqlite3

omnis_db = r'str(Path(__file__).resolve().parent.parent.parent)\knowledge\memory\unified_memory.db'
conn = sqlite3.connect(omnis_db)
cur = conn.cursor()

print("All Jarvis entries in LAIS:")
cur.execute("SELECT id, agent, category, key, value FROM memory_entries WHERE agent='jarvis'")
for r in cur.fetchall():
    print(f"  ID={r[0]} category={r[2]} key={r[3]}")
    print(f"  value preview: {r[4][:80]}...")
    print()

print("\nAll entries in LAIS:")
cur.execute("SELECT id, agent, category, key FROM memory_entries")
for r in cur.fetchall():
    print(f"  {r[0]}: agent={r[1]} cat={r[2]} key={r[3]}")

conn.close()
