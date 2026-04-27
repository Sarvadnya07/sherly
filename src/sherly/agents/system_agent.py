import json
import time
from sherly.tools.automation_tools import open_app, type_text
from sherly.tools.terminal_tools import safe_exec
import pyautogui
from sherly.agents.base_agent import BaseAgent

_SYSTEM_PROMPT = """\
You are an AI system automation agent with God-level OS control.
Convert the user's request into a JSON list of actions to execute on a Windows PC.

Available actions:
- {"action": "open_app", "app": "name of application"} (e.g. notepad, calculator)
- {"action": "type_text", "text": "text to type"}
- {"action": "press_key", "key": "key name"} (e.g. enter, win, esc, tab, space, up, down)
- {"action": "media_control", "command": "playpause" | "volumeup" | "volumedown" | "nexttrack" | "prevtrack" | "volumemute"} 
- {"action": "hotkey", "keys": ["ctrl", "c"]} (presses multiple keys at once)
- {"action": "wait", "seconds": 1.5}
- {"action": "run_command", "cmd": "shell command"}

Examples:
"play pause video" -> [{"action": "media_control", "command": "playpause"}]
"increase volume" -> [{"action": "media_control", "command": "volumeup"}, {"action": "media_control", "command": "volumeup"}]
"copy this" -> [{"action": "hotkey", "keys": ["ctrl", "c"]}]
"open calculator and press 5" -> [{"action": "open_app", "app": "calculator"}, {"action": "wait", "seconds": 1.5}, {"action": "type_text", "text": "5"}]

Output strictly JSON and nothing else.
Request: {text}
"""

def _parse_actions(text: str, ask_model):
    raw = ask_model(_SYSTEM_PROMPT.format(text=text), store_history=False, use_context=False)
    
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
        
    try:
        return json.loads(raw)
    except Exception:
        return []


class SystemAgent(BaseAgent):
    def run(self, prompt: str, ask_model=None) -> str:
        if not ask_model:
            return safe_exec(prompt)
            
        actions = _parse_actions(prompt, ask_model)
        if not actions:
            return safe_exec(prompt)
            
        executed = []
        
        for act in actions:
            try:
                a_type = act.get("action")
                if a_type == "open_app":
                    app = act.get("app", "")
                    open_app(app)
                    executed.append(f"Opened {app}")
                elif a_type == "type_text":
                    text = act.get("text", "")
                    type_text(text)
                    executed.append(f"Typed '{text[:20]}...'")
                elif a_type == "press_key":
                    key = act.get("key", "")
                    pyautogui.press(key)
                    executed.append(f"Pressed {key}")
                elif a_type == "media_control":
                    cmd = act.get("command", "")
                    pyautogui.press(cmd)
                    executed.append(f"Media command: {cmd}")
                elif a_type == "hotkey":
                    keys = act.get("keys", [])
                    if keys:
                        pyautogui.hotkey(*keys)
                        executed.append(f"Hotkey {'+'.join(keys)}")
                elif a_type == "wait":
                    sec = act.get("seconds", 1)
                    time.sleep(float(sec))
                    executed.append(f"Waited {sec}s")
                elif a_type == "run_command":
                    cmd = act.get("cmd", "")
                    safe_exec(cmd)
                    executed.append(f"Ran '{cmd}'")
            except Exception as e:
                executed.append(f"Failed {act}: {e}")
                
        return "\n".join(executed) if executed else "No valid actions performed."
