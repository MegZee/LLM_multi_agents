import json
import os
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def ensure_data_dir():
    """Ensures the data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_session(session_data):
    """Saves the full session data to a JSON file."""
    ensure_data_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = session_data.get("session_id", "unknown")
    filename = f"session_{timestamp}_{session_id}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    with open(filepath, "w") as f:
        json.dump(session_data, f, indent=2)
    
    return filepath
