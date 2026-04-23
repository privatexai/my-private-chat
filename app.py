import streamlit as st
import sqlite3
from datetime import datetime
from google import genai
from google.genai import types

# --- 1. INITIALIZATION & UI ---
st.set_page_config(page_title="JARVIS v12.6", page_icon="🛡️", layout="wide")

# Corrected Markdown styling
st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; }
    .stChatMessage { border-radius: 10px; border: 1px solid #00d4ff; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

SYSTEM_INSTRUCTION = "You are JARVIS, an elite British AI. Be proactive and address the user as 'Sir'."

# --- 2. THE CORE CLIENT (2026 SDK) ---
try:
    # Use the new Client structure to avoid genai.configure issues
    client = genai.Client(api_key=st.secrets["GEMINI_KEY"])
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
except Exception as e:
    st.error(f"Critical System Failure: Secrets not found. {e}")
    st.stop()

# --- 3. ARCHIVE PROTOCOL ---
def init_db():
    conn = sqlite3.connect('jarvis_v12_6.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history(role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()

# --- 4. SECURITY GATE ---
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if not st.session_state.unlocked:
    st.markdown("<h1 style='text-align:center;'>TERMINAL ENCRYPTED</h1>", unsafe_allow_html=True)
    gate_input = st.text_input("PASSWORD REQUIRED", type="password")
    if st.button("Unlock"):
        if gate_input == MASTER_PASSCODE:
            st.session_state.unlocked = True
            st.rerun()
        else:
            st.error("ACCESS DENIED")
    st.stop()

# --- 5. CHAT STREAM ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history ORDER BY timestamp ASC')
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. NEURAL EXECUTION ---
prompt = st.chat_input("Direct me, Sir...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # Modern Tool Configuration
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[
                    types.Tool(google_search=types.GoogleSearch()),
                    types.Tool(code_execution=types.CodeExecution())
                ]
            )

            with st.spinner("Processing..."):
                # Flash-Lite is the optimized 2026 driver
                response = client.models.generate_content(
                    model='gemini-2.0-flash-lite', 
                    contents=prompt,
                    config=config
                )
                response_text = response.text

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            c.execute('INSERT INTO history(role, content, timestamp) VALUES (?,?,?)', 
                      ("assistant", response_text, datetime.now()))
            conn.commit()

        except Exception as e:
            st.error(f"Logic Breach: {e}")
