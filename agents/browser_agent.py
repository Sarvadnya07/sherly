from web_search import search_web


def run(prompt, ask_model):
    results = search_web(prompt)
    return ask_model(
        f"""
Summarize this information:

{results}
"""
    )
