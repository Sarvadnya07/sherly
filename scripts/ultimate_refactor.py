import os
import re

def ultimate_refactor():
    root = "src/sherly"
    
    # Mapping of module name to new package path
    mappings = {
        'action_manager': 'sherly.services.action_manager',
        'agent_manager': 'sherly.services.agent_manager',
        'command_router': 'sherly.services.command_router',
        'config_manager': 'sherly.config.config_manager',
        'conversation_memory': 'sherly.services.conversation_memory',
        'input_validator': 'sherly.core.input_validator',
        'model_manager': 'sherly.services.model_manager',
        'runtime_utils': 'sherly.utils.runtime_utils',
        'speech_to_text': 'sherly.services.speech_to_text',
        'text_to_speech': 'sherly.services.text_to_speech',
        'memory': 'sherly.services.memory',
        'memory_brain': 'sherly.services.memory_brain',
        'notifier': 'sherly.services.notifier',
        'plugin_loader': 'sherly.core.plugin_loader',
        'plugin_manager': 'sherly.core.plugin_manager',
        'safety_guard': 'sherly.core.safety_guard',
        'tool_registry': 'sherly.core.tool_registry',
        'web_search': 'sherly.services.web_search',
        'task_scheduler': 'sherly.core.task_scheduler',
        'diagnostics': 'sherly.core.diagnostics',
        'model_scanner': 'sherly.services.model_scanner',
        'core': 'sherly.core',
        'agents': 'sherly.agents',
        'routers': 'sherly.routers',
        'tools': 'sherly.tools',
        'sherly_ui': 'sherly.ui',
        'sherly_ai': 'sherly.sherly_ai',
        'sherly_commands': 'sherly.sherly_commands',
        'sherly_core': 'sherly.sherly_core',
        'sherly_utils': 'sherly.sherly_utils',
    }

    # Patterns to match:
    # 1. from <mod> import ...
    # 2. import <mod>
    # 3. <mod>.<attr> (if it's a direct import)
    
    for subdir, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(subdir, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = content
                for mod, new_path in mappings.items():
                    # Replace "from mod" but NOT "from sherly.services.mod"
                    # We use negative lookbehind for "sherly." or "from "
                    # Actually, a simpler way: replace if it's at start of line or after space, and not preceded by "sherly."
                    
                    # Pattern for "from mod"
                    from_pattern = r'(?<!\.)\bfrom ' + re.escape(mod) + r'\b'
                    new_content = re.sub(from_pattern, f'from {new_path}', new_content)
                    
                    # Pattern for "import mod"
                    import_pattern = r'(?<!\.)\bimport ' + re.escape(mod) + r'\b'
                    new_content = re.sub(import_pattern, f'import {new_path}', new_content)
                    
                    # Special case for "tools.X"
                    if mod == 'tools':
                        tools_pattern = r'(?<!sherly\.)\btools\.'
                        new_content = re.sub(tools_pattern, 'sherly.tools.', new_content)

                if new_content != content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Refactored: {path}")

if __name__ == "__main__":
    ultimate_refactor()
