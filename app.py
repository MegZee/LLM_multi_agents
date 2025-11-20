import streamlit as st
import time
from backend.config import load_topics, get_topic_by_id
from backend.storage import save_session
from backend.agents import ProfilerAgent, PersuaderAgent

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
    st.title("Persuasion Chatbot Demo")
    st.write("Choose a topic to discuss.")
    
    topics = load_topics()
    for topic in topics:
        with st.container(border=True):
            st.subheader(topic["title"])
            st.write(topic["description"])
            if st.button(f"Select {topic['title']}", key=topic["id"]):
                st.session_state.topic = topic
                set_page("PRE_CHAT")

def pre_chat_page():
    st.title("Pre-Chat Survey")
    st.write(f"Topic: **{st.session_state.topic['title']}**")
    st.write("Please answer the following questions (0 = Strongly Disagree, 10 = Strongly Agree).")
    
    answers = {}
    for q in st.session_state.topic["questions"]:
        answers[q] = st.slider(q, 0, 10, 5)
    
    if st.button("Start Chat"):
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
    st.title(f"Chat: {st.session_state.topic['title']}")
    
    # Display chat history
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    # User input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to history
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # Profiler Step
        with st.status("Analyzing...", expanded=False):
            new_profile = st.session_state.profiler.analyze(
                prompt, 
                st.session_state.history, 
                st.session_state.topic["description"]
            )
            st.session_state.profile = new_profile
            st.write("Profile Updated:", new_profile)
            
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
        with st.chat_message("assistant"):
            st.write(reply)
            
    # End Chat Button
    if len(st.session_state.history) >= 2: # Allow ending after some interaction
        if st.button("Finish Conversation"):
            set_page("POST_CHAT")

def post_chat_page():
    st.title("Post-Chat Survey")
    st.write("Now that you've discussed the topic, please answer the questions again.")
    
    answers = {}
    for q in st.session_state.topic["questions"]:
        answers[q] = st.slider(q, 0, 10, 5, key=f"post_{q}")
        
    if st.button("Submit"):
        st.session_state.post_survey = answers
        save_data()
        set_page("END")

def end_page():
    st.title("Thank You!")
    st.write("Your responses have been recorded.")
    
    st.subheader("Results")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Pre-Chat")
        st.write(st.session_state.pre_survey)
    with col2:
        st.write("Post-Chat")
        st.write(st.session_state.post_survey)
        
    if st.button("Start Over"):
        st.session_state.clear()
        set_page("LANDING")

def save_data():
    session_data = {
        "topic": st.session_state.topic,
        "pre_survey": st.session_state.pre_survey,
        "post_survey": st.session_state.post_survey,
        "history": st.session_state.history,
        "final_profile": st.session_state.profile
    }
    save_session(session_data)

def main():
    init_session()
    
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

def admin_page():
    st.title("Admin Configuration")
    
    if st.button("Back to Home"):
        set_page("LANDING")
        
    st.subheader("Manage Topics")
    
    topics = load_topics()
    
    # Add New Topic
    with st.expander("Add New Topic"):
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
        with st.expander(f"Edit: {topic['title']}"):
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
        if st.button("Admin Panel"):
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
