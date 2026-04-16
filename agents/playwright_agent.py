"""
God-Level Browser Automation Agent using Playwright.
Provides autonomous DOM interaction, element tagging, and complex web navigation.
"""
import json
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    pass  # Let it crash only when run is called if not installed

# The Javascript to run inside the browser page to label all interactive elements
_INJECT_JS = """
() => {
    let elements = [];
    let idCounter = 0;

    // Remove old labels if they exist
    document.querySelectorAll('.sherly-label').forEach(e => e.remove());

    const interactables = document.querySelectorAll('a, button, input, textarea, select, [role="button"], [role="link"], [tabindex]:not([tabindex="-1"])');
    
    interactables.forEach(el => {
        const rect = el.getBoundingClientRect();
        // Only consider elements visible on screen
        if (rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.top <= window.innerHeight) {
            
            // Generate a unique ID (just an integer)
            const id = idCounter++;
            el.setAttribute('data-sherly-id', id);
            
            // Draw a label overlay for visual debugging
            const overlay = document.createElement('div');
            overlay.className = 'sherly-label';
            overlay.style.position = 'fixed';
            overlay.style.left = (rect.left) + 'px';
            overlay.style.top = (rect.top) + 'px';
            overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
            overlay.style.color = 'white';
            overlay.style.fontSize = '12px';
            overlay.style.fontWeight = 'bold';
            overlay.style.padding = '1px 3px';
            overlay.style.zIndex = '9999999';
            overlay.style.pointerEvents = 'none'; // Don't block clicks
            overlay.innerText = `[${id}]`;
            
            document.body.appendChild(overlay);
            
            elements.push({
                id: id,
                tag: el.tagName.toLowerCase(),
                text: el.innerText ? el.innerText.substring(0, 50).replace(/\\n/g, ' ') : (el.value || el.placeholder || ""),
                role: el.getAttribute('role') || '',
                type: el.getAttribute('type') || ''
            });
        }
    });

    return elements;
}
"""

_AGENT_PROMPT = """\
You are a God-Level autonomous browser agent. You are currently viewing a webpage.
The user wants you to: "{goal}"

Current URL: {url}
Page Title: {title}

Visible Interactive Elements (Tagged with [ID]):
{elements}

Select your next action to accomplish the user's goal.
Output EXACTLY ONE JSON object from the following choices:
- {{"action": "CLICK", "id": 5}}
- {{"action": "TYPE", "id": 3, "text": "something"}}
- {{"action": "SCROLL_DOWN"}}
- {{"action": "SCROLL_UP"}}
- {{"action": "GO_BACK"}}
- {{"action": "DONE", "result": "The answer or summary of what you did"}}

Do not provide extra text. Only JSON.
"""

_URL_PROMPT = """\
The user wants to do a browser task: "{goal}"
What is the best starting URL for this task?
Output ONLY a raw URL starting with https://. If general search, use https://www.google.com
"""

def extract_json(raw: str) -> dict:
    import re
    raw = raw.replace("```json", "").replace("```", "").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
        raw = re.sub(r',\s*}', '}', raw)
        raw = re.sub(r',\s*\]', ']', raw)
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {}

def run(prompt: str, ask_model) -> str:
    # 1. Ask LLM for the starting URL
    url_raw = ask_model(_URL_PROMPT.format(goal=prompt), store_history=False, use_context=False)
    starting_url = url_raw.strip().split()[0]
    if not starting_url.startswith("http"):
        starting_url = "https://www.google.com"

    # Start the robust browser session
    try:
        if 'sync_playwright' not in globals():
            return "Error: Playwright is not properly installed or imported."
            
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            try:
                page.goto(starting_url, timeout=15000)
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass # ignore timeouts and proceed

        max_steps = 10
        result = "Max steps reached without finishing."

        for step in range(max_steps):
            
            # Allow page to settle completely before scraping interactive elements
            page.wait_for_timeout(3000)

            # Inject JS to label elements and get data
            elements = []
            try:
                elements = page.evaluate(_INJECT_JS)
            except Exception as e:
                print(f"Error evaluating JS: {e}")
                
            # Format elements for LLM
            elem_text = ""
            for el in elements:
                desc = f"Tag: {el['tag']}"
                if el['text']: desc += f", Text: '{el['text']}'"
                if el['type']: desc += f", Type: {el['type']}"
                elem_text += f"[ID: {el['id']}] {desc}\n"

            if not elem_text:
                elem_text = "No interactive elements visible."

            # Construct the current state prompt
            state_prompt = _AGENT_PROMPT.format(
                goal=prompt,
                url=page.url,
                title=page.title(),
                elements=elem_text
            )

            # Get action from LLM
            raw_response = ask_model(state_prompt, store_history=False, use_context=False)
            action_json = extract_json(raw_response)

            if not action_json:
                print(f"[Browser Agent] Invalid action received: {raw_response}")
                # Try scrolling down if stuck
                action_json = {"action": "SCROLL_DOWN"}

            act = action_json.get("action", "")
            
            try:
                if act == "DONE":
                    result = action_json.get("result", "Finished the task.")
                    break
                elif act == "CLICK":
                    target_id = action_json.get("id")
                    page.evaluate(f"document.querySelector('[data-sherly-id=\"{target_id}\"]').click()")
                    # page.wait_for_load_state("networkidle", timeout=5000)
                elif act == "TYPE":
                    target_id = action_json.get("id")
                    text_to_type = action_json.get("text", "")
                    
                    # Need to click into it, then fill
                    # Using evaluate since direct Playwright dispatch might fail if DOM changed slightly
                    selector = f"[data-sherly-id=\"{target_id}\"]"
                    page.locator(selector).fill(text_to_type)
                    page.locator(selector).press("Enter")
                elif act == "SCROLL_DOWN":
                    page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                elif act == "SCROLL_UP":
                    page.evaluate("window.scrollBy(0, -window.innerHeight * 0.8)")
                elif act == "GO_BACK":
                    page.go_back()
                else:
                    action_json = {"action": "SCROLL_DOWN"}
            except Exception as e:
                print(f"[Browser Agent] Failed action {act}: {e}")
                
            page.wait_for_timeout(2000)

        browser.close()
        return f"Browser Automation complete: {result}"
        
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"Playwright Critical Error:\n{trace}")
        return f"Browser automation failed: {str(e)}"
