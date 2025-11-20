# LLM_multi_agents

A Streamlit-based web application featuring two collaborating LLM agents:
- **Profiler**: Analyzes user survey answers and chat messages to build a psychological profile.
- **Persuader**: Uses the profile to generate personalized persuasive arguments.

## Setup

1.  Install dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```
2.  Set up `.env` with your `GEMINI_API_KEY`.
3.  Run the app:
    ```bash
    streamlit run app.py
    ```
