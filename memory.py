import sqlite3

# --- Database Initialization ---
conn = sqlite3.connect("sherly_memory.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS memory (key TEXT UNIQUE, value TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY, user TEXT, assistant TEXT)")
conn.commit()


def add_memory(user_text, assistant_text):
    """Persist each exchange so future prompts can reference recent context."""
    conn.execute(
        "INSERT INTO chat_history (user, assistant) VALUES (?, ?)",
        (user_text, assistant_text)
    )
    conn.commit()


def get_context(limit=5):
    """Return the last few exchanges formatted for prompt injection."""
    cursor = conn.execute(
        "SELECT user, assistant FROM chat_history ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()[::-1]

    history = ""
    for user, assistant in rows:
        history += f"User: {user}\nAssistant: {assistant}\n"
    return history.strip()


def save_memory(key, value):
    """Store persistent key/value data (settings, API keys, etc.)."""
    conn.execute(
        "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
        (key, str(value))
    )
    conn.commit()


def get_memory(key):
    """Retrieve a stored setting by key."""
    cursor = conn.execute(
        "SELECT value FROM memory WHERE key=?",
        (key,)
    )
    result = cursor.fetchone()
    return result[0] if result else None
