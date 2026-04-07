"""Registry for lightweight text tools such as plugins."""

tools = []


def register_tool(name, function):
    tools.append((name.lower(), function))


def run_tool(text, payload=None):
    normalized = text.lower()
    for name, func in tools:
        if name in normalized:
            return func(payload if payload is not None else text)
    return None


def clear_tools():
    tools.clear()
