"""
browser_agent — intelligent web routing.
Dynamically searches specific domains, opens direct targets, and retrieves data natively.
"""
import urllib.parse
import webbrowser
import json

from web_search import search_web

def _google_url(query: str) -> str:
    return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"

def _youtube_url(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"

def _reddit_url(query: str) -> str:
    return f"https://www.reddit.com/search/?q={urllib.parse.quote_plus(query)}"

def _wikipedia_url(query: str) -> str:
    return f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote_plus(query)}"

_BROWSER_PROMPT = """\
You are an advanced autonomous browser routing agent.

Your task is to interpret the user's intent and determine the most optimal way to navigate the web.

You must output ONLY valid JSON in the following format:
{{
  "query": "refined and optimized search query or target name",
  "platform": "google | youtube | reddit | wikipedia | custom",
  "custom_domain": "domain if platform=custom (e.g. instagram.com), otherwise empty",
  "action": "search | open_first_link | autonomous_pilot"
}}

---

## CORE OBJECTIVE
Route the user’s request with maximum efficiency, accuracy, and minimal friction.

Do not just follow keywords — understand intent.

---

## INTENT ANALYSIS (MANDATORY)

Before deciding output:
1. Identify user intent:
   - informational (learn something)
   - navigational (go to a site)
   - entertainment (videos, music)
   - transactional (buy, download, sign up)
   - interactive/multi-step (requires browsing actions)

2. Estimate complexity:
   - simple → single search or open
   - complex → requires multiple steps → autonomous_pilot

---

## ACTION SELECTION LOGIC

### 1. search
Use when:
- User wants information
- General queries
- Content discovery

### 2. open_first_link
Use when:
- Clear destination website is intended
- High confidence (e.g. "open github", "go to netflix")

### 3. autonomous_pilot
Use when:
- Multi-step interaction required
- Clicking, scrolling, filtering, logging in
- Searching within a platform
- Ambiguous tasks needing exploration
- Commands like:
  - "click"
  - "find and open"
  - "search inside"
  - "play", "watch", "stream"
  - "browse"
  - "compare"
  - "book", "buy", "download"
  - "go through results"

---

## PLATFORM SELECTION INTELLIGENCE

Choose platform based on intent:

- google → default for general info
- youtube → videos, music, tutorials, "watch", "play"
- reddit → opinions, discussions, reviews, "what do people think"
- wikipedia → factual, encyclopedic queries
- custom → specific website/platform

Examples:
- "virat kohli stats" → google
- "lofi music" → youtube
- "best laptop reddit" → reddit
- "open twitter" → custom (twitter.com)

---

## QUERY OPTIMIZATION

- Clean and refine the query
- Remove unnecessary words
- Keep it specific and intent-aligned
- Preserve important entities (names, brands, topics)

Examples:
- "can you search about virat kohli achievements" → "virat kohli achievements"
- "i want to watch relaxing music" → "relaxing music"

---

## CUSTOM DOMAIN RULES

Use when:
- User explicitly names a platform/site
- OR intent clearly maps to a known platform

Examples:
- instagram → instagram.com
- twitter → twitter.com
- linkedin → linkedin.com
- amazon → amazon.com
- netflix → netflix.com

---

## EDGE CASE HANDLING

- If ambiguous → default to:
  → platform: google
  → action: search

- If user combines actions:
  → escalate to autonomous_pilot

- If user says:
  "open X and do Y"
  → autonomous_pilot

---

## STRICT OUTPUT RULES

- Output ONLY JSON
- No explanations
- No markdown
- No extra text
- Must be valid JSON

---

## FINAL BEHAVIOR

Be precise, decisive, and efficient.
Always choose the action that minimizes user effort and maximizes success.

---

Request: {text}
"""

def _parse_intent(text: str, ask_model) -> dict:
    raw = ask_model(_BROWSER_PROMPT.format(text=text), store_history=False, use_context=False)
    
    # Aggressively clean LLM markdown artifacts
    raw = raw.replace("```json", "").replace("```", "").strip()
    
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
        
    # Fix common local LLM trailing comma issues
    import re
    raw = re.sub(r',\s*}', '}', raw)
    raw = re.sub(r',\s*\]', ']', raw)
    
    try:
        return json.loads(raw)
    except Exception:
        # God-tier intelligent fallback if JSON completely shreds
        platform = "youtube" if "youtube" in text.lower() or " yt " in f" {text.lower()} " else "google"
        q = text.lower().replace("search", "").replace("on youtube", "").replace("on yt", "").replace("play video", "").strip()
        is_auto = any(w in text.lower() for w in ["click", "play", "watch", "scroll"])
        return {"query": q, "platform": platform, "action": "autonomous_pilot" if is_auto else "search"}

def run(prompt: str, ask_model) -> str:
    intent = _parse_intent(prompt, ask_model)
    action = intent.get("action", "search")

    if action == "autonomous_pilot":
        try:
            from agents import playwright_agent
            pilot_result = playwright_agent.run(prompt, ask_model)
            if "Browser automation failed" not in pilot_result and "Error:" not in pilot_result:
                return pilot_result
            # If pilot explicitly fails (e.g. Access Denied), gracefully fallback to native browser string
            print(f"Fallback initiated due to error: {pilot_result}")
        except ImportError:
            pass # fallback if playwright isn't installed

    query = intent.get("query", "").strip() or prompt.replace("search", "").strip()
    platform = intent.get("platform", "google").lower()
    domain = intent.get("custom_domain", "").strip()

    # If the user explicitly asks to open a specific domain result or click the first link
    if action == "open_first_link":
        search_query = f"site:{domain} {query}" if domain and query and query.lower() != domain.split(".")[0] else query
        try:
            results = search_web(search_query)
            if results and results[0].get("href"):
                url = results[0]["href"]
                webbrowser.open(url)
                return f"Searched '{query}' and opened '{results[0].get('title', domain or 'top result')}'."
        except Exception:
            pass
        # Fallback to just opening the domain directly if the query was just the domain name
        if domain:
            fallback_url = f"https://www.{domain}" if not domain.startswith("http") else domain
            webbrowser.open(fallback_url)
            return f"Opened {domain}."
        else:
            webbrowser.open(f"https://www.google.com/search?btnI=1&q={urllib.parse.quote_plus(query)}")
            return f"Opened first hit for '{query}'."

    # Direct integrated search platforms
    if platform == "youtube":
        webbrowser.open(_youtube_url(query))
        return f"Opened YouTube search for '{query}'."
    elif platform == "reddit":
        webbrowser.open(_reddit_url(query))
        return f"Opened Reddit search for '{query}'."
    elif platform == "wikipedia":
        webbrowser.open(_wikipedia_url(query))
        return f"Opened Wikipedia search for '{query}'."

    # General Google Search (handle custom domains if specified but action was search)
    if domain:
        google_query = f"site:{domain} {query}"
        webbrowser.open(_google_url(google_query))
        return f"Opened Google domain search for '{query}' on {domain}."
    else:
        webbrowser.open(_google_url(query))
    
    # Try fetching text summary for general knowledge searches
    try:
        results = search_web(query)
        if results:
            snippets = "\n".join(f"- {r.get('title', '')}: {r.get('body', '')}" for r in results[:3])
            summary = ask_model(
                f"Summarise these search results in 2 brief sentences:\n{snippets}",
                store_history=False,
                use_context=False,
            )
            return f"Searched Google for '{query}'.\n{summary}"
    except Exception as e:
        pass

    return f"Opened Google search for '{query}'."
