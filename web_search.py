from ddgs import DDGS

def search_web(query):

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))

    return results