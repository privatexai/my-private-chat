import streamlit as st
import sqlite3
import time
from datetime import datetime
from google import genai
from google.genai import types

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="JARVIS v12.5", page_icon="🛡️", layout="wide")

# Custom CSS for the Terminal Look
st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; }
    .stChatMessage { border-radius: 10px; border: 1px solid #00d4ff; }
    </style>
""", unsafe_allow_html=True)

SYSTEM_INSTRUCTION = """
You are JARVIS, an elite British AI for Sir Admin.
- Use Google Search for live data and real-time news.
- Use Code Execution for math and algorithms.
- Always address the user as 'Sir'.
"""

# --- 2. AUTHENTICATION & CLIENT ---
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"Hardware Error: Credentials missing or invalid. {e}")
    st.stop()

# --- 3. DATABASE ARCHIVE ---
def init_db():
    conn = sqlite3.connect('jarvis_v12_5.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history(user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()
USER_ID = "Admin_Sir"

# --- 4. SECURITY GATE ---
if "gate_unlocked" not in st.session_state:
    st.session_state.gate_unlocked = False

if not st.session_state.gate_unlocked:
    st.markdown("<h1 style='text-align:center;'>SYSTEM ENCRYPTED</h1>", unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        gate_input = st.text_input("ENTER MASTER PASSCODE", type="password")
        if st.button("Unlock Terminal", use_container_width=True):
            if gate_input == MASTER_PASSCODE:
                st.session_state.gate_unlocked = True
                st.rerun()
            else:
                st.error("ACCESS DENIED.")
    st.stop()

# --- 5. CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. THE THINKING CORE ---
prompt = st.chat_input("Direct JARVIS, Sir...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # 2026 Tool Setup
            search_tool = types.Tool(google_search=types.GoogleSearch())
            code_tool = types.Tool(code_execution=types.CodeExecution())
            
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[search_tool, code_tool],
                temperature=0.7
            )

            with st.spinner("Analyzing data streams..."):
                response = client.models.generate_content(
                    model='gemini-2.0-flash-lite', # Using the ultra-stable 2026 lite core
                    contents=prompt,
                    config=config
                )
                response_text = response.text

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
                      (USER_ID, "assistant", response_text, datetime.now()))
            conn.commit()

            # Voice Feedback
            audio_text = response_text[:150].replace(' ', '%20').replace('"', '')
            voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={audio_text}&tl=en-gb&client=tw-ob"
            st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)

        except Exception as e:
            st.error(f"Logic Failure: {e}")
