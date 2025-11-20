import streamlit as st
import time
from backend.config import load_topics, get_topic_by_id
from backend.storage import save_session
from backend.agents import ProfilerAgent, PersuaderAgent

# Page Config
st.set_page_config(
    page_title="Persuasion Chatbot",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
def load_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }
        
        .stButton>button {
            border-radius: 20px;
            border: 1px solid #E0E0E0;
            background-color: #FFFFFF;
            color: #333333;
            font-weight: 600;
            padding: 0.5rem 1.5rem;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            border-color: #4CAF50;
            color: #4CAF50;
            background-color: #F9F9F9;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .topic-card {
            padding: 1.5rem;
            border-radius: 15px;
            background-color: #F8F9FA;
            border: 1px solid #E9ECEF;
            margin-bottom: 1rem;
            transition: transform 0.2s;
        }
        
        .topic-card:hover {
            transform: scale(1.02);
            border-color: #4CAF50;
        }
        
        h1 {
            font-weight: 700 !important;
            color: #1A1A1A;
        }
        
        h2, h3 {
            font-weight: 600 !important;
            color: #333333;
        }
        
        .stChatMessage {
            background-color: transparent;
        }
        
        div[data-testid="stChatMessageContent"] {
            border-radius: 15px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        div[data-testid="stChatMessageContent"] p {
            margin-bottom: 0;
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

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

def set_page(page_name):
    st.session_state.page = page_name
    st.rerun()

def landing_page():
    st.title("💬 Persuasion Chatbot")
    st.markdown("### Choose a topic to start the conversation")
    st.markdown("---")
    
    topics = load_topics()
    
    # Grid Layout
    cols = st.columns(len(topics))
    
    for i, topic in enumerate(topics):
        with cols[i]:
            with st.container(border=True):
                st.subheader(topic["title"])
                st.caption(topic["description"])
                st.markdown("<br>", unsafe_allow_html=True)
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
        st.markdown(f"**{q}**")
        answers[q] = st.slider("", 0, 10, 5, key=q, help="0 = Strongly Disagree, 10 = Strongly Agree")
        st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Chat", use_container_width=True, type="primary"):
            st.session_state.pre_survey = answers
            
            with st.spinner("Analyzing your responses..."):
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
    st.title(f"🗣️ {st.session_state.topic['title']}")
    
    # Sidebar Context
    with st.sidebar:
        st.header("Session Info")
        st.markdown(f"**Topic:** {st.session_state.topic['title']}")
        if "stance" in st.session_state.profile:
            st.markdown(f"**Detected Stance:** {st.session_state.profile['stance'].title()}")
        
        if st.button("End Conversation", type="primary", use_container_width=True):
            set_page("POST_CHAT")

    # Display chat history
    for msg in st.session_state.history:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            
    # User input
    if prompt := st.chat_input("Type your message..."):
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
            st.write("Updated Profile:", new_profile)
            
        # Persuader Step
        with st.spinner("Thinking..."):
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
        st.markdown(f"**{q}**")
        answers[q] = st.slider("", 0, 10, 5, key=f"post_{q}")
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
    
    st.subheader("Your Journey")
    
    # Calculate changes
    pre = st.session_state.pre_survey
    post = st.session_state.post_survey
    
    questions = list(pre.keys())
    
    for q in questions:
        pre_score = pre.get(q, 0)
        post_score = post.get(q, 0)
        diff = post_score - pre_score
        
        delta_color = "normal"
        if diff > 0: delta_color = "off" # Greenish usually, but Streamlit delta colors are specific
        elif diff < 0: delta_color = "inverse"
        
        st.metric(label=q, value=f"{post_score}/10", delta=f"{diff:+}", delta_color="normal")
        
    st.markdown("---")
    if st.button("Start New Session", type="primary"):
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
    
    # Sidebar for Admin Access
    with st.sidebar:
        if st.button("⚙️ Admin Panel"):
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
