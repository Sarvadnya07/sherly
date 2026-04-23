import os
import re

def refactor_tests():
    root = "tests"
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
    }
    
    for subdir, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(subdir, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = content
                for mod, new_path in mappings.items():
                    from_pattern = r'(?<!\.)\bfrom ' + re.escape(mod) + r'\b'
                    new_content = re.sub(from_pattern, f'from {new_path}', new_content)
                    import_pattern = r'(?<!\.)\bimport ' + re.escape(mod) + r'\b'
                    new_content = re.sub(import_pattern, f'import {new_path}', new_content)

                if new_content != content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Refactored test: {path}")

if __name__ == "__main__":
    refactor_tests()
