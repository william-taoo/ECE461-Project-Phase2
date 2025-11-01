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


def find_model_in_registry(registry, model_id: str):
    for model in registry:
        if model["id"] == model_id:
            return model

    return None
