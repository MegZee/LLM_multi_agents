import json
import os

TOPICS_FILE = os.path.join(os.path.dirname(__file__), "topics.json")

def load_topics():
    """Loads topics from the JSON configuration file."""
    if not os.path.exists(TOPICS_FILE):
        return []
    
    with open(TOPICS_FILE, "r") as f:
        return json.load(f)

def get_topic_by_id(topic_id):
    """Retrieves a specific topic by its ID."""
    topics = load_topics()
    for topic in topics:
        if topic["id"] == topic_id:
            return topic
    return None
