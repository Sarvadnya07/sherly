import json

MEMORY_FILE = "memory.json"


def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)


def remember(key, value):
    mem = load_memory()
    mem[key] = value
    save_memory(mem)
    return f"I will remember that {key} is {value}"


def recall(key):
    mem = load_memory()
    return mem.get(key, "I don't know that yet.")
