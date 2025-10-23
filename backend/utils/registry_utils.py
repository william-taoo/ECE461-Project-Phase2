import json
import os

def load_registry(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
        
def save_registry(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)