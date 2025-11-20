import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

class ProfilerAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def analyze(self, user_message, history, topic_description):
        prompt = f"""
        You are a Profiler Agent. Your task is to analyze the user's latest message and the conversation history to build a psychological profile.
        
        Topic: {topic_description}
        
        History:
        {json.dumps(history, indent=2)}
        
        Latest User Message: "{user_message}"
        
        Output a JSON object with the following fields:
        - stance: "pro" or "anti" (relative to the topic)
        - confidence_in_stance: 0.0 to 1.0
        - tone: e.g., "formal", "casual", "sarcastic", "emotional"
        - emotional_state: e.g., "neutral", "frustrated", "excited"
        - persuasion_strategy: A list of strategies to use (e.g., ["appeal_to_values", "provide_evidence"])
        - style_guidelines: Short advice for the responder (e.g., "be empathetic", "use facts")
        
        Return ONLY the JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Clean up potential markdown formatting
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except Exception as e:
            print(f"Profiler Error: {e}")
            return {
                "stance": "unknown",
                "confidence": 0.0,
                "tone": "neutral",
                "emotional_state": "neutral",
                "persuasion_strategy": ["default"],
                "style_guidelines": "be polite"
            }

    def analyze_survey(self, survey_answers, topic_description):
        # Calculate average score
        scores = list(survey_answers.values())
        avg_score = sum(scores) / len(scores) if scores else 5
        
        derived_stance = "neutral"
        if avg_score < 4:
            derived_stance = "strongly against"
        elif avg_score < 6:
            derived_stance = "neutral/mixed"
        else:
            derived_stance = "strongly in favor"

        prompt = f"""
        You are a Profiler Agent. Analyze the user's pre-chat survey answers to build an initial profile.
        
        Topic: {topic_description}
        
        Survey Answers (0=Strongly Disagree, 10=Strongly Agree):
        {json.dumps(survey_answers, indent=2)}
        
        Calculated Average Score: {avg_score:.1f} / 10
        Derived Stance: {derived_stance}
        
        Output a JSON object with:
        - stance: "{derived_stance}"
        - confidence_in_stance: 0.0 to 1.0 (High if scores are consistent)
        - tone: "neutral"
        - emotional_state: "neutral"
        - persuasion_strategy: "Start by acknowledging their {derived_stance} position, then gently introduce a counter-point."
        - style_guidelines: "Be conversational but direct. Don't overwhelm with facts yet."
        
        Return ONLY the JSON.
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except Exception as e:
            print(f"Profiler Survey Error: {e}")
            return {"stance": derived_stance, "confidence": 0.5}

class PersuaderAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def generate_opening(self, profile, topic_description, survey_answers):
        prompt = f"""
        You are a Persuader Agent. You are starting a conversation with a user about a topic.
        
        Topic: {topic_description}
        
        User Profile:
        {json.dumps(profile, indent=2)}
        
        Instructions:
        1. Acknowledge their general stance based on the profile (e.g., "I see that you are generally against...").
        2. Immediately pivot to a persuasive counter-point or "did you know" fact.
        3. Example structure: "I see you lean towards [Stance]. But did you know that [Counter-Fact]? What do you think about that?"
        4. Keep it short (max 2 sentences).
        5. Do NOT be aggressive, but be challenging.
        
        Generate the opening message only.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Persuader Opening Error: {e}")
            return f"I see your stance on {topic_description}. Have you considered the alternative view?"

    def generate_reply(self, user_message, history, profile, topic_description):
        prompt = f"""
        You are a Persuader Agent. Your goal is to gently persuade the user to change their mind about the topic.
        
        Topic: {topic_description}
        
        User Profile (inferred):
        {json.dumps(profile, indent=2)}
        
        Conversation History:
        {json.dumps(history, indent=2)}
        
        Latest User Message: "{user_message}"
        
        Instructions:
        1. Adopt the opposite stance to the user.
        2. Use the 'persuasion_strategy' and 'style_guidelines' from the profile.
        3. Be conversational, respectful, and concise (max 2-3 sentences).
        4. Do not lecture. Ask thought-provoking questions if appropriate.
        
        Generate the response text only.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Persuader Error: {e}")
            return "I see. Tell me more about your perspective."
