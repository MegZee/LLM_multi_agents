import streamlit as st
import time
import json
from backend.config import load_topics, get_topic_by_id
from backend.storage import save_session
from backend.agents import ProfilerAgent, PersuaderAgent

# Page Config
st.set_page_config(
    page_title="Persuasion Chatbot",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="auto"
)

# Dark Mode Toggle
def toggle_theme():
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    
    with st.sidebar:
        st.markdown("### 🎨 Theme")
        theme_choice = st.radio("", ["☀️ Light", "🌙 Dark"], 
                                index=0 if st.session_state.theme == "light" else 1,
                                horizontal=True,
                                label_visibility="collapsed")
        st.session_state.theme = "light" if "Light" in theme_choice else "dark"

# Custom CSS with Dark Mode Support
def load_css():
    theme = st.session_state.get("theme", "light")
    
    if theme == "dark":
        bg_color = "#0E1117"
        card_bg = "#1E2127"
        text_color = "#FAFAFA"
        border_color = "#3A3F4B"
        accent_color = "#4CAF50"
        hover_bg = "#262B35"
    else:
        bg_color = "#FFFFFF"
        card_bg = "#F8F9FA"
        text_color = "#1A1A1A"
        border_color = "#E9ECEF"
        accent_color = "#4CAF50"
        hover_bg = "#F0F0F0"
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"]  {{
            font-family: 'Inter', sans-serif;
            background-color: {bg_color};
            color: {text_color};
        }}
        
        .stApp {{
            background-color: {bg_color};
        }}
        
        .stButton>button {{
            border-radius: 25px;
            border: 2px solid {border_color};
            background-color: {card_bg};
            color: {text_color};
            font-weight: 600;
            padding: 0.75rem 2rem;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .stButton>button:hover {{
            border-color: {accent_color};
            color: {accent_color};
            background-color: {hover_bg};
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(76, 175, 80, 0.2);
        }}
        
        .topic-card {{
            padding: 2rem;
            border-radius: 20px;
            background: linear-gradient(135deg, {card_bg} 0%, {hover_bg} 100%);
            border: 2px solid {border_color};
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}
        
        .topic-card:hover {{
            transform: translateY(-4px);
            border-color: {accent_color};
            box-shadow: 0 8px 24px rgba(76, 175, 80, 0.15);
        }}
        
        /* Likert Scale Styling */
        .stSlider {{
            padding: 1rem 0;
        }}
        
        .stSlider > div > div > div > div {{
            background-color: {accent_color};
        }}
        
        .likert-container {{
            background-color: {card_bg};
            padding: 1.5rem;
            border-radius: 15px;
            margin-bottom: 1rem;
            border: 1px solid {border_color};
        }}
        
        .likert-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            color: {text_color};
            opacity: 0.7;
            margin-top: 0.5rem;
        }}
        
        h1 {{
            font-weight: 700 !important;
            color: {text_color};
            background: linear-gradient(135deg, {accent_color} 0%, #45a049 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        h2, h3 {{
            font-weight: 600 !important;
            color: {text_color};
        }}
        
        /* Chat Message Styling */
        .stChatMessage {{
            background-color: transparent !important;
            padding: 1rem 0;
        }}
        
        div[data-testid="stChatMessageContent"] {{
            border-radius: 20px;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            background-color: {card_bg};
            border: 1px solid {border_color};
        }}
        
        div[data-testid="stChatMessageContent"] p {{
            margin-bottom: 0;
            line-height: 1.6;
        }}
        
        /* Chat Input */
        .stChatInputContainer {{
            border-top: 2px solid {border_color};
            padding-top: 1rem;
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {card_bg};
            border-right: 2px solid {border_color};
        }}
        
        /* Info boxes */
        .stAlert {{
            border-radius: 15px;
            border-left: 4px solid {accent_color};
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
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

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
    st.markdown(f"""
        <div class="likert-container">
            <p style="font-weight: 600; margin-bottom: 1rem;">{question}</p>
        </div>
    """, unsafe_allow_html=True)
    
    value = st.slider(
        "",
        0, 10, 5,
        key=f"{key_prefix}{question}",
        label_visibility="collapsed"
    )
    
    st.markdown("""
        <div class="likert-labels">
            <span>Strongly Disagree</span>
            <span>Neutral</span>
            <span>Strongly Agree</span>
        </div>
    """, unsafe_allow_html=True)
    
    return value

def landing_page():
    st.title("💬 Persuasion Chatbot")
    st.markdown("### Choose a topic to start the conversation")
    st.markdown("---")
    
    topics = load_topics()
    
    # Grid Layout
    cols = st.columns(len(topics))
    
    for i, topic in enumerate(topics):
        with cols[i]:
            st.markdown(f"""
                <div class="topic-card">
                    <h3 style="margin-bottom: 0.5rem;">{topic["title"]}</h3>
                    <p style="opacity: 0.8; font-size: 0.9rem;">{topic["description"]}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select", key=topic["id"], use_container_width=True):
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
    st.title(f"💬 {st.session_state.topic['title']}")
    
    # Sidebar Context
    with st.sidebar:
        st.markdown("### 📊 Session Info")
        st.markdown(f"**Topic:** {st.session_state.topic['title']}")
        if "stance" in st.session_state.profile:
            stance = st.session_state.profile['stance'].title()
            st.markdown(f"**Your Stance:** {stance}")
        
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
    toggle_theme()
    load_css()
    
    # Sidebar for Admin Access
    with st.sidebar:
        st.markdown("---")
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
        admin_page()

if __name__ == "__main__":
    main()
