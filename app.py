import streamlit as st
import time
import json
from backend.config import load_topics, get_topic_by_id
from backend.storage import save_session
from backend.agents import ProfilerAgent, PersuaderAgent

# Page Config
st.set_page_config(
    page_title="DOXA",
    page_icon="💭",
    layout="centered",
    initial_sidebar_state="auto"
)

# Custom CSS - Claude-inspired Grey Theme
def load_css():
    bg_color = "#1E1E1E"
    card_bg = "#2C2C2C"
    text_color = "#E0E0E0"
    border_color = "#3A3A3A"
    accent_color = "#D97706"
    hover_bg = "#353535"
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Inter:wght@400;500;600&display=swap');
        
        html, body, [class*="css"]  {{
            font-family: 'Merriweather', serif;
            background-color: {bg_color};
            color: {text_color};
            font-size: 16px;
            line-height: 1.7;
        }}
        
        .stApp {{
            background-color: {bg_color};
        }}
        
        .stButton>button {{
            border-radius: 12px;
            border: 1px solid {border_color};
            background-color: {card_bg};
            color: {text_color};
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            padding: 0.75rem 1.5rem;
            transition: all 0.2s ease;
        }}
        
        .stButton>button:hover {{
            border-color: {accent_color};
            background-color: {hover_bg};
            transform: translateY(-1px);
        }}
        
        /* Chat Messages - Claude style (no bubbles for assistant) */
        .stChatMessage {{
            background-color: transparent !important;
            padding: 1.5rem 0;
            border: none !important;
        }}
        
        /* Assistant messages - plain text, no bubble */
        .stChatMessage[data-testid="assistant-message"] div[data-testid="stChatMessageContent"] {{
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            box-shadow: none !important;
        }}
        
        /* User messages - subtle dark bubble */
        .stChatMessage[data-testid="user-message"] div[data-testid="stChatMessageContent"] {{
            background-color: #2A2A2A !important;
            border-radius: 20px;
            padding: 0.75rem 1rem !important;
            border: 1px solid {border_color};
            max-width: 80%;
            margin-left: auto;
        }}
        
        div[data-testid="stChatMessageContent"] p {{
            margin-bottom: 0;
            line-height: 1.7;
            color: {text_color};
            font-family: 'Merriweather', serif;
        }}
        
        /* Slider customization for gradient effect */
        .stSlider > div > div > div > div {{
            background: linear-gradient(90deg, 
                #EF4444 0%,
                #F97316 25%,
                #EAB308 50%,
                #84CC16 75%,
                #22C55E 100%
            ) !important;
        }}
        
        .stSlider > div > div > div {{
            background-color: #3A3A3A !important;
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {card_bg};
            border-right: 1px solid {border_color};
        }}
        
        /* Input styling */
        .stChatInputContainer {{
            border-top: 1px solid {border_color};
            padding-top: 1rem;
            background-color: {bg_color};
        }}
        
        input, textarea {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
            border-color: {border_color} !important;
            font-family: 'Inter', sans-serif !important;
        }}
        
        h1, h2, h3 {{
            color: {text_color};
            font-family: 'Inter', sans-serif;
        }}
        
        h1 {{
            font-weight: 600 !important;
        }}
        
        /* Info boxes */
        .stAlert {{
            background-color: {card_bg};
            border-left: 4px solid {accent_color};
            color: {text_color};
        }}
        </style>
    """, unsafe_allow_html=True)

# Initialize Agents
if "profiler" not in st.session_state:
    st.session_state.profiler = ProfilerAgent()
if "persuader" not in st.session_state:
    st.session_state.persuader = PersuaderAgent()

def init_session():
    if "page" not in st.session_state:
        st.session_state.page = "LANDING"
    if "history" not in st.session_state:
        st.session_state.history = []
    if "profile" not in st.session_state:
        st.session_state.profile = {}
    if "topic" not in st.session_state:
        st.session_state.topic = None
    if "pre_survey" not in st.session_state:
        st.session_state.pre_survey = {}
    if "post_survey" not in st.session_state:
        st.session_state.post_survey = {}

def is_localhost():
    """Check if running on localhost - only show admin on local development"""
    import os
    # Check multiple Streamlit Cloud indicators
    if (os.getenv("STREAMLIT_SHARING_MODE") or 
        os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud" or
        os.path.exists("/mount/src")):  # Streamlit Cloud uses /mount/src
        return False
    return True

def set_page(page_name):
    st.session_state.page = page_name
    st.rerun()

def save_data():
    session_data = {
        "session_id": "unknown",
        "topic": st.session_state.topic,
        "pre_survey": st.session_state.pre_survey,
        "post_survey": st.session_state.post_survey,
        "history": st.session_state.history,
        "final_profile": st.session_state.profile
    }
    save_session(session_data)

def render_likert_scale(question, key_prefix=""):
    # Get or initialize the value
    state_key = f"likert_{key_prefix}{question}"
    if state_key not in st.session_state:
        st.session_state[state_key] = 5
    
    # HTML for the emoji scale - using simple string concatenation to avoid indentation issues
    html_content = f"""
    <div style="background-color: #2C2C2C; padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem; border: 1px solid #3A3A3A;">
        <p style="font-weight: 600; margin-bottom: 1.5rem; color: #E0E0E0; font-size: 1.1rem;">{question}</p>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">😢</div>
                <div style="color: #999; font-size: 0.8rem;">Strongly<br>Disagree</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">😕</div>
                <div style="color: #999; font-size: 0.8rem;">Disagree</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">😐</div>
                <div style="color: #999; font-size: 0.8rem;">Neutral</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🙂</div>
                <div style="color: #999; font-size: 0.8rem;">Agree</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">😄</div>
                <div style="color: #999; font-size: 0.8rem;">Strongly<br>Agree</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)
    
    # Slider with gradient background
    value = st.slider(
        "Select your agreement level (1-10)",
        1, 10, st.session_state[state_key],
        key=f"slider_{key_prefix}{question}",
        label_visibility="collapsed"
    )
    
    # Update session state
    st.session_state[state_key] = value
    
    return value

def landing_page():
    st.title("💭 DOXA")
    st.markdown("### Explore Different Perspectives")
    st.markdown("""
    DOXA challenges your viewpoints by presenting alternative angles on controversial topics.  
    Engage in a conversation designed to broaden your perspective and test the strength of your beliefs.
    """)
    st.markdown("---")
    
    topics = load_topics()
    
    # Grid Layout with clickable cards
    cols = st.columns(len(topics))
    
    for i, topic in enumerate(topics):
        with cols[i]:
            # Make the entire card a button
            if st.button(
                f"**{topic['title']}**\n\n{topic['description']}", 
                key=topic["id"], 
                use_container_width=True,
                type="secondary"
            ):
                st.session_state.topic = topic
                set_page("PRE_CHAT")

def pre_chat_page():
    st.title("📝 Pre-Chat Survey")
    st.info(f"Topic: **{st.session_state.topic['title']}**")
    st.write("Please answer the following questions to help us understand your perspective.")
    st.markdown("---")
    
    answers = {}
    for q in st.session_state.topic["questions"]:
        answers[q] = render_likert_scale(q)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Chat", use_container_width=True, type="primary"):
            st.session_state.pre_survey = answers
            
            with st.spinner("🧠 Analyzing your responses..."):
                # Initial profile analysis
                initial_profile = st.session_state.profiler.analyze_survey(
                    answers, 
                    st.session_state.topic["description"]
                )
                st.session_state.profile = initial_profile
                
                # Generate icebreaker
                opening_msg = st.session_state.persuader.generate_opening(
                    initial_profile,
                    st.session_state.topic["description"],
                    answers
                )
                
                # Add to history
                st.session_state.history = [{"role": "assistant", "content": opening_msg}]
                
            set_page("CHAT")

def chat_page():
    st.title(f"💭 {st.session_state.topic['title']}")
    
    # Sidebar Context
    with st.sidebar:
        st.markdown("### 📊 Session Info")
        st.markdown(f"**Topic:** {st.session_state.topic['title']}")
        
        st.markdown("---")
        if st.button("🏁 End Conversation", type="primary", use_container_width=True):
            set_page("POST_CHAT")

    # Display chat history with enhanced styling
    for msg in st.session_state.history:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            
    # User input
    if prompt := st.chat_input("💭 Type your message..."):
        # Add user message to history
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.write(prompt)
            
        # Profiler Step
        with st.status("🧠 Analyzing...", expanded=False):
            new_profile = st.session_state.profiler.analyze(
                prompt, 
                st.session_state.history, 
                st.session_state.topic["description"]
            )
            st.session_state.profile = new_profile
            st.write("Profile Updated")
            
        # Persuader Step
        with st.spinner("💭 Thinking..."):
            reply = st.session_state.persuader.generate_reply(
                prompt,
                st.session_state.history,
                st.session_state.profile,
                st.session_state.topic["description"]
            )
            
        # Add bot message to history
        st.session_state.history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant", avatar="🤖"):
            st.write(reply)

def post_chat_page():
    st.title("📋 Post-Chat Survey")
    st.write("Now that you've discussed the topic, has your opinion changed?")
    st.markdown("---")
    
    answers = {}
    for q in st.session_state.topic["questions"]:
        answers[q] = render_likert_scale(q, "post_")
        
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Submit Results", use_container_width=True, type="primary"):
            st.session_state.post_survey = answers
            save_data()
            set_page("END")

def end_page():
    st.balloons()
    st.title("🎉 Thank You!")
    st.success("Your responses have been recorded.")
    
    st.subheader("📈 Your Journey")
    
    # Calculate changes
    pre = st.session_state.pre_survey
    post = st.session_state.post_survey
    
    questions = list(pre.keys())
    
    for q in questions:
        pre_score = pre.get(q, 0)
        post_score = post.get(q, 0)
        diff = post_score - pre_score
        
        st.metric(label=q, value=f"{post_score}/10", delta=f"{diff:+}")
        
    st.markdown("---")
    if st.button("🔄 Start New Session", type="primary"):
        st.session_state.clear()
        set_page("LANDING")

def admin_page():
    st.title("⚙️ Admin Configuration")
    
    if st.button("← Back to Home"):
        set_page("LANDING")
        
    st.subheader("Manage Topics")
    
    topics = load_topics()
    
    # Add New Topic
    with st.expander("➕ Add New Topic"):
        new_id = st.text_input("Topic ID (unique)")
        new_title = st.text_input("Title")
        new_desc = st.text_area("Description")
        new_q1 = st.text_input("Question 1")
        new_q2 = st.text_input("Question 2")
        new_q3 = st.text_input("Question 3")
        
        if st.button("Add Topic"):
            if new_id and new_title and new_q1:
                new_topic = {
                    "id": new_id,
                    "title": new_title,
                    "description": new_desc,
                    "questions": [q for q in [new_q1, new_q2, new_q3] if q]
                }
                topics.append(new_topic)
                with open("backend/topics.json", "w") as f:
                    json.dump(topics, f, indent=2)
                st.success("Topic added!")
                st.rerun()
            else:
                st.error("Please fill in ID, Title, and at least one question.")

    # Edit Existing Topics
    for i, topic in enumerate(topics):
        with st.expander(f"✏️ Edit: {topic['title']}"):
            e_title = st.text_input("Title", topic["title"], key=f"t_{i}")
            e_desc = st.text_area("Description", topic["description"], key=f"d_{i}")
            
            # Simple text area for questions (one per line)
            q_text = "\n".join(topic["questions"])
            e_qs = st.text_area("Questions (one per line)", q_text, key=f"q_{i}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes", key=f"save_{i}"):
                    topics[i]["title"] = e_title
                    topics[i]["description"] = e_desc
                    topics[i]["questions"] = [q.strip() for q in e_qs.split("\n") if q.strip()]
                    with open("backend/topics.json", "w") as f:
                        json.dump(topics, f, indent=2)
                    st.success("Saved!")
                    st.rerun()
            with col2:
                if st.button("Delete Topic", key=f"del_{i}", type="primary"):
                    topics.pop(i)
                    with open("backend/topics.json", "w") as f:
                        json.dump(topics, f, indent=2)
                    st.success("Deleted!")
                    st.rerun()

def main():
    init_session()
    load_css()
    
    # Admin Panel - Only visible on localhost
    if is_localhost():
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🔧 Developer Tools")
            if st.button("⚙️ Admin Panel", use_container_width=True):
                set_page("ADMIN")
    
    if st.session_state.page == "LANDING":
        landing_page()
    elif st.session_state.page == "PRE_CHAT":
        pre_chat_page()
    elif st.session_state.page == "CHAT":
        chat_page()
    elif st.session_state.page == "POST_CHAT":
        post_chat_page()
    elif st.session_state.page == "END":
        end_page()
    elif st.session_state.page == "ADMIN":
        if is_localhost():
            admin_page()
        else:
            st.error("Admin panel is only accessible on localhost.")
            set_page("LANDING")

if __name__ == "__main__":
    main()
