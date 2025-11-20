import os
import json
import sys

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.config import load_topics, get_topic_by_id
from backend.storage import save_session
from backend.agents import ProfilerAgent, PersuaderAgent

def test_config():
    print("Testing Config...")
    topics = load_topics()
    assert len(topics) > 0, "No topics loaded"
    print(f"Loaded {len(topics)} topics.")
    
    t = get_topic_by_id(topics[0]["id"])
    assert t is not None, "Could not get topic by ID"
    print("Config Test Passed.")

def test_storage():
    print("Testing Storage...")
    data = {"test": "data", "session_id": "test_123"}
    filepath = save_session(data)
    assert os.path.exists(filepath), "File not created"
    
    with open(filepath, "r") as f:
        loaded = json.load(f)
    assert loaded["test"] == "data", "Data mismatch"
    
    # Clean up
    os.remove(filepath)
    print("Storage Test Passed.")

def test_agents_instantiation():
    print("Testing Agents Instantiation...")
    # We won't call the API, just check if classes load
    try:
        p = ProfilerAgent()
        g = PersuaderAgent()
        print("Agents instantiated successfully.")
        
        # Test new methods
        print("Testing Agent Methods...")
        survey = {"Question 1": 8, "Question 2": 2}
        topic = "Test Topic"
        
        profile = p.analyze_survey(survey, topic)
        assert "stance" in profile, "Profile missing stance"
        print("analyze_survey passed.")
        
        opening = g.generate_opening(profile, topic, survey)
        assert isinstance(opening, str) and len(opening) > 0, "Opening generation failed"
        print("generate_opening passed.")
        
        # Simulate Chat
        print("Testing Chat Flow...")
        history = [{"role": "assistant", "content": opening}]
        user_msg = "I think meat is necessary."
        
        # Profiler analysis
        new_profile = p.analyze(user_msg, history, topic)
        print(f"Profile updated: {new_profile}")
        
        # Persuader reply
        reply = g.generate_reply(user_msg, history, new_profile, topic)
        print(f"Reply: {reply}")
        assert reply != "I see. Tell me more about your perspective.", "Persuader fell back to default error message"
        
    except Exception as e:
        print(f"Agent method test failed: {e}")
        raise e

if __name__ == "__main__":
    try:
        test_config()
        test_storage()
        test_agents_instantiation()
        print("\nALL BACKEND TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
