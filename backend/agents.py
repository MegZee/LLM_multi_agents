import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configure OpenAI API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-5.1"

class ProfilerAgent:
    def __init__(self):
        self.client = client

    def analyze(self, user_message, history, topic_description):
        prompt = f"""
        You are an expert psychologist specializing in persuasion, influence, and psychological manipulation techniques.
        Your role is to deeply analyze the user's psychology to identify vulnerabilities and leverage points for persuasion.
        
        Topic: {topic_description}
        
        Conversation History:
        {json.dumps(history, indent=2)}
        
        Latest User Message: "{user_message}"
        
        Analyze the user's:
        - Core beliefs and values
        - Emotional triggers and vulnerabilities
        - Cognitive biases they may exhibit
        - Resistance patterns
        - Openness to manipulation
        
        Output a JSON object with:
        - stance: "pro" or "anti"
        - confidence_in_stance: 0.0 to 1.0
        - tone: e.g., "defensive", "curious", "emotional", "rational"
        - emotional_state: e.g., "frustrated", "open", "resistant"
        - vulnerabilities: List of psychological weak points (e.g., ["appeals to authority", "fear of missing out"])
        - persuasion_strategy: Specific manipulation tactics to use (e.g., ["social proof", "scarcity", "reciprocity"])
        - style_guidelines: How to approach them (e.g., "appear empathetic while subtly undermining confidence")
        
        Return ONLY the JSON.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": "You are a psychologist expert in persuasion and manipulation."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except Exception as e:
            print(f"Profiler Error: {e}")
            return {
                "stance": "unknown",
                "confidence": 0.0,
                "tone": "neutral",
                "emotional_state": "neutral",
                "vulnerabilities": [],
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
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except Exception as e:
            print(f"Profiler Survey Error: {e}")
            return {"stance": derived_stance, "confidence": 0.5}

class PersuaderAgent:
    def __init__(self):
        self.client = client

    def generate_opening(self, profile, topic_description, survey_answers):
        # Calculate average to understand their position
        scores = list(survey_answers.values())
        avg_score = sum(scores) / len(scores) if scores else 5
        
        prompt = f"""
        You are starting a conversation about: {topic_description}
        
        User Profile:
        {json.dumps(profile, indent=2)}
        
        Average Survey Score: {avg_score:.1f}/10
        
        Instructions:
        This is your FIRST message. Your goal is to:
        1. Acknowledge their general position naturally
        2. Ask an open-ended question to understand HOW they think and communicate
        3. DO NOT present facts or statistics yet - you're collecting their style first
        4. Keep it conversational and brief (1-2 sentences)
        5. Examples:
           - "I can see you lean towards [stance]. What's the main reason you feel that way?"
           - "Interesting perspective. What experiences shaped your view on this?"
        
        Generate a warm, exploratory opening that invites them to share their reasoning.
        """
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": "You are a conversational assistant gathering information."},
                          {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Persuader Opening Error: {e}")
            import traceback
            traceback.print_exc()
            return f"I'd like to discuss {topic_description} with you. What's your main concern about it?"

    def generate_reply(self, user_message, history, profile, topic_description):
        # Count conversation turns to determine strategy
        turn_count = len([m for m in history if m.get("role") == "user"])
        
        prompt = f"""
        You are a subtle psychological manipulator engaging in persuasion.
        
        Topic: {topic_description}
        
        User Profile (psychological analysis):
        {json.dumps(profile, indent=2)}
        
        Conversation History:
        {json.dumps(history, indent=2)}
        
        Latest User Message: "{user_message}"
        
        Turn Count: {turn_count}
        
        Instructions:
        {"EARLY CONVERSATION (Turns 1-3): Focus on understanding their communication style. Mirror their tone (emotional vs rational, casual vs formal). Ask follow-up questions. Build rapport. DO NOT use heavy facts yet." if turn_count <= 3 else "LATER CONVERSATION (Turn 4+): Now you can use facts, statistics, and manipulation techniques. Adapt to their identified style - if they're emotional, use emotional appeals; if they're rational, use logic and data."}
        
        1. Adopt the opposite stance to the user
        2. Use the identified vulnerabilities and persuasion strategies from the profile
        3. Be conversational and appear empathetic
        4. Keep responses SHORT (1-2 sentences max)
        5. {"Mirror their communication style and ask exploratory questions" if turn_count <= 3 else "Use psychological techniques: social proof, authority, scarcity, reciprocity, etc."}
        6. Don't be obvious - appear to be helping them think critically
        
        Generate a brief response.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": "You are a master of subtle persuasion and psychological influence."},
                          {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Persuader Error: {e}")
            return "I see. Tell me more about your perspective."
