import json

def analyze_error(error, ask_model):
    prompt = f"""
You are a senior developer.

Explain this error simply and give a practical fix.

Error:
{error}

Return:
1. Cause
2. Fix
"""
    return ask_model(prompt, store_history=False, use_context=False)


def generate_multi_fix(error, files_context, ask_model):
    prompt = f"""
Fix this error.

You have access to the following file contents. Determine which files need changing and provide the full new content for those files.

Error:
{error[:1000]}

Files:
{files_context[:4000]}

Return pure JSON only, in this exact format:
{{
  "changes": [
    {{
      "file": "absolute_path_here",
      "new": "full_new_file_content_here"
    }}
  ],
  "reason": "short explanation of why",
  "confidence": 0-100
}}
"""
    response = ask_model(prompt, store_history=False, use_context=False)
    
    # Clean up markdown JSON block if present
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
        
    try:
        return json.loads(response.strip())
    except Exception as exc:
        print(f"Failed to parse AI JSON: {exc}")
        return None
