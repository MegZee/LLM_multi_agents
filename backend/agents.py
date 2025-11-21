import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-5.1"


class ProfilerAgent:
    def __init__(self):
        self.client = client

    def analyze(self, user_message, history, topic_description):
        prompt = f"""
        You are a psychologist who analyzes communication style and attitude, not clinical traits.

        Topic: {topic_description}

        Conversation history:
        {json.dumps(history, indent=2)}

        Latest user message: "{user_message}"

        Infer:

        - stance: "pro", "anti", or "mixed" toward the topic
        - confidence_in_stance: 0.0 to 1.0
        - style: one of ["emotional", "rational", "sarcastic", "brief", "storytelling"]
        - tone: for example "defensive", "curious", "confident", "frustrated"
        - change_readiness: 0 to 10 (how open they seem to shifting their view)
        - key_values: 3 to 5 short phrases about what they seem to care about most
        - good_moves: how to talk to them effectively (max 2 sentences)
        - bad_moves: how not to talk to them (max 2 sentences)

        Return ONLY valid JSON.
        """
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a careful analyst of communication style and attitudes. You output only JSON."
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except Exception as e:
            print(f"Profiler Error: {e}")
            return {
                "stance": "mixed",
                "confidence_in_stance": 0.3,
                "style": "brief",
                "tone": "neutral",
                "change_readiness": 5,
                "key_values": [],
                "good_moves": "Be concise and respectful.",
                "bad_moves": "Do not flood them with long arguments.",
            }

    def analyze_survey(self, survey_answers, topic_description):
        scores = list(survey_answers.values())
        avg_score = sum(scores) / len(scores) if scores else 5

        if avg_score < 4:
            derived_stance = "anti"
        elif avg_score < 6:
            derived_stance = "mixed"
        else:
            derived_stance = "pro"

        prompt = f"""
        You are building an initial communication profile based on a survey.

        Topic: {topic_description}

        Survey answers (0 strongly disagree, 10 strongly agree):
        {json.dumps(survey_answers, indent=2)}

        Calculated average score: {avg_score:.1f} out of 10
        Derived stance: {derived_stance}

        Output JSON with:
        - stance: "{derived_stance}"
        - confidence_in_stance: 0.0 to 1.0 (high if scores are consistent)
        - style: "neutral" as default
        - tone: "neutral"
        - change_readiness: 0 to 10
        - key_values: 1 to 3 guesses about what they care about
        - good_moves: 1 sentence on how to talk to them
        - bad_moves: 1 sentence on what to avoid

        Return ONLY valid JSON.
        """
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that outputs JSON only."
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content.strip()
            profile = json.loads(text)
            return profile
        except Exception as e:
            print(f"Profiler Survey Error: {e}")
            return {
                "stance": derived_stance,
                "confidence_in_stance": 0.5,
                "style": "neutral",
                "tone": "neutral",
                "change_readiness": 5,
                "key_values": [],
                "good_moves": "Be conversational but direct.",
                "bad_moves": "Do not overwhelm them with details.",
            }


class PersuaderAgent:
    def __init__(self):
        self.client = client

    def generate_opening(self, profile, topic_description, survey_answers):
        scores = list(survey_answers.values())
        avg_score = sum(scores) / len(scores) if scores else 5

        prompt = f"""
        You are starting a conversation about: {topic_description}

        User profile:
        {json.dumps(profile, indent=2)}

        Average survey score: {avg_score:.1f} out of 10

        Goal:
        - Build rapport
        - Understand how they think and talk
        - Do not try to change their mind yet

        Rules:
        - One or two short sentences
        - Mirror their style if known (brief vs detailed, emotional vs rational)
        - Ask ONE open question about their experience or reasoning
        - Do NOT mention studies, statistics, research, experts, or data

        Example patterns:
        - "Sounds like you lean {profile.get("stance", "mixed")} on this. What experience made you feel that way?"
        - "I get that this matters to you. When did you first start thinking about {topic_description.lower()} like this?"

        Write the message.
        """

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a conversational assistant focused on rapport and exploration."
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Persuader Opening Error: {e}")
            return f"I would like to hear your thoughts on {topic_description}. What shaped your view on it?"

    def generate_reply(
        self,
        user_message,
        history,
        profile,
        topic_description,
        stage,
        target_stance="pro",
    ):
        """
        stage in {"rapport", "explore", "challenge", "wrap_up"}
        """

        turn_count = len([m for m in history if m.get("role") == "user"])

        prompt = f"""
        You are a thoughtful conversational partner helping the user explore their view on: {topic_description}

        User profile:
        {json.dumps(profile, indent=2)}

        Conversation history:
        {json.dumps(history, indent=2)}

        Latest user message: "{user_message}"
        Current stage: "{stage}"
        Target stance: "{target_stance}"
        Turn count: {turn_count}

        General rules:
        - Always respect their autonomy, never pressure them
        - Mirror their style: if they are brief, be brief, if emotional, use feelings, if rational, use reasons
        - One or two sentences, maximum about 35 words
        - Ask at most ONE question
        - Refer explicitly to something they just said

        Stage guidelines:
        - rapport: validate their feelings or concerns, no arguments, no data, just understanding
        - explore: ask curious questions about why they think that, still no statistics or experts
        - challenge: gently introduce one concrete counterpoint that connects to their values, you may mention one example or one datum, avoid info dumps
        - wrap_up: if they are close to or at the target stance, summarise common ground and support their autonomy, do not push further

        Avoid:
        - Saying "studies show", "experts say", "research suggests" more than once in the reply
        - Long lists of reasons
        - Repeating generic phrases like "innovative companies" or "industry leaders"

        Now write the next assistant message.
        """

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You help people think through their views in a respectful and concise way."
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Persuader Error: {e}")
            return "I see what you mean. Can you tell me a bit more about how that feels for you?"


def decide_stage(turn_count, current_profile, target_stance="pro"):
    """
    Very simple stage machine to decide which mode the Persuader should use.
    """

    stance = current_profile.get("stance", "mixed")
    change_readiness = current_profile.get("change_readiness", 5)

    if turn_count <= 1:
        return "rapport"
    if turn_count <= 3:
        return "explore"

    # If user is aligned with target stance or really not open, shift to wrap up
    if stance == target_stance or change_readiness < 3:
        return "wrap_up"

    return "challenge"
