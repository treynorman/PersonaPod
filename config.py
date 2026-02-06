import json
import os
from dotenv import dotenv_values

# Load constants from .env
env_vars = dotenv_values(".env")

# Parse system prompts and lists
def parse_value(key, value):
    # Handle system prompts
    # If string starts with a relative path to the prompts directory,
    #  return the full contents of the text, including special characters
    if isinstance(value, str) and (value.startswith("./prompts") or value.startswith("prompts")) and os.path.exists(value):
        with open(value, "r", encoding="utf-8") as f:
            return f.read()

    # Handle lists
    # If string starts with '[', try to parse it as a JSON list
    if isinstance(value, str) and value.strip().startswith('['):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # If it looks like a list but is broken, just return the string
            return value

    # CASE C: Standard string
    return value

# 3. Inject processed variables into global scope
for key, value in env_vars.items():
    globals()[key] = parse_value(key, value)