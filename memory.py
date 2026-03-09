import sqlite3

conn = sqlite3.connect("sherly_memory.db")

def save_memory(key, value):

    conn.execute(
        "INSERT INTO memory VALUES (?, ?)",
        (key, value)
    )

    conn.commit()

def get_memory(key):

    cursor = conn.execute(
        "SELECT value FROM memory WHERE key=?",
        (key,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return None