import os
import json
import builtins


def load_test_data(sub_dir):
    """
    Loads test data from a JSON file in the specified subdirectory.
    """
    # Path to Logic/API/ai/{sub_dir}/testData.json
    path = os.path.join(
        builtins.PROJECT_ROOT, "Logic", "API", "ai", sub_dir, "testData.json"
    )

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Test data file not found: {path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from: {path}")
        return {}
