import streamlit as st
import google.generativeai as genai
import sqlite3
from datetime import datetime

# --- 1. HARD-CODED FAST REPLIES ---
FAST_REPLIES = {
    "hello": "Hello, Sir. Systems are nominal. How can I assist?",
    "hi": "Hi there, Sir. Ready for your next command.",
    "how are you": "Operational and optimized, Sir. Thank you for asking.",
    "status": "All systems secure. Encryption active. Gemini 2.5 Flash core is humming.",
    "who are you": "I am JARVIS, your private analytical core.",
}

SYSTEM_INSTRUCTION = """
You are JARVIS. When a user provides a link (YouTube, Instagram, Facebook), 
your priority is to analyze the context of that URL. 
- Summarize the likely content based on the URL structure and metadata.
- If it's a YouTube link, discuss it as a visual data stream.
- If it's social media, analyze the digital footprint/intent of the post.
Always maintain your British, sophisticated persona.
"""

# --- 2. SYSTEM SETUP ---
st.set_page_config(page_title="JARVIS TERMINAL", page_icon="🛡️")

try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("Vault Error: Credentials Missing.")
    st.stop()

# --- 3. DATABASE ---
def init_db():
    conn = sqlite3.connect('jarvis_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history(user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()
USER_ID = "Admin_Sir"

# --- 4. PASSCODE GATE ---
if "gate_unlocked" not in st.session_state:
    st.session_state.gate_unlocked = False

if not st.session_state.gate_unlocked:
    st.markdown("<h1 style='text-align:center;'>SYSTEM ENCRYPTED</h1>", unsafe_allow_html=True)
    gate_input = st.text_input("ENTER MASTER PASSCODE", type="password")
    if st.button("Unlock"):
        if gate_input == MASTER_PASSCODE:
            st.session_state.gate_unlocked = True
            st.rerun()
    st.stop()

# --- 5. CHAT ENGINE ---
st.title("JARVIS: INSTANT CORE")

if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. FAST & DEEP PROCESSING ---
prompt = st.chat_input("Direct JARVIS, Sir...")

if prompt:
    # Save User Prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', (USER_ID, "user", prompt, datetime.now()))
    conn.commit()

    # Step A: Check for Fast Reply
    lower_prompt = prompt.lower().strip().replace("?", "")
    if lower_prompt in FAST_REPLIES:
        response_text = FAST_REPLIES[lower_prompt]
    else:
        # Step B: Deep Analysis (AI)
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=SYSTEM_INSTRUCTION
            )
            response = model.generate_content(prompt)
            response_text = response.text
        except Exception as e:
            response_text = f"Core Error, Sir: {str(e)}"

    # Display and Save Assistant Response
    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', (USER_ID, "assistant", response_text, datetime.now()))
    conn.commit()

    # Audio Protocol
    voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={response_text[:200].replace(' ', '%20')}&tl=en-gb&client=tw-ob"
    st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)
