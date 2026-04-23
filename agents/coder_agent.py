def run(prompt, ask_model):
    return ask_model(
        f"""
You are a coding expert.

Task:
{prompt}

Explain, fix, or improve code.
"""
    )
