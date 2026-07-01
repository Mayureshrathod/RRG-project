import sqlite3
conn = sqlite3.connect('data/cache_metadata.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())
