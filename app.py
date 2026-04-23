import streamlit as st
import google.generativeai as genai
import sqlite3
import os
from datetime import datetime

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="JARVIS TERMINAL", page_icon="🛡️", layout="centered")

# Retrieve secrets from Streamlit Vault
try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except Exception as e:
    st.error("CRITICAL ERROR: Secrets (ACCESS_CODE or GEMINI_KEY) missing in Streamlit Cloud.")
    st.stop()

# --- 2. DATABASE ENGINE (VERSION 2 - ERROR PROOF) ---
def init_db():
    # Renaming to v2.db forces the server to create a fresh, correct table
    conn = sqlite3.connect('jarvis_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)''')
    conn.commit()
    return conn, c

conn, c = init_db()
USER_ID = "Admin_Sir"

# --- 3. SECURITY GATE ---
if "gate_unlocked" not in st.session_state:
    st.session_state.gate_unlocked = False

if not st.session_state.gate_unlocked:
    st.markdown("<h1 style='text-align:center; color:#00d4ff;'>REMOTELY ENCRYPTED TERMINAL</h1>", unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        gate_input = st.text_input("ENTER MASTER PASSCODE", type="password")
        if st.button("Unlock Gate", use_container_width=True):
            if gate_input == MASTER_PASSCODE:
                st.session_state.gate_unlocked = True
                st.rerun()
            else:
                st.error("ACCESS DENIED: Internal Security Triggered.")
    st.stop()

# --- 4. INTERFACE & HISTORY ---
st.title("JARVIS: ANALYTICAL CORE")

with st.sidebar:
    st.markdown("### 🛡️ SYSTEM STATUS: SECURE")
    if st.button("Emergency Lock"):
        st.session_state.gate_unlocked = False
        st.rerun()

# Initialize session messages and load from DB
if "messages" not in st.session_state:
    st.session_state.messages = []
    try:
        c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
        for row in c.fetchall():
            st.session_state.messages.append({"role": row[0], "content": row[1]})
    except Exception as e:
        st.error(f"Memory Retrieval Error: {e}")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. AI PROCESSING CORE ---
prompt = st.chat_input("Input data for analysis, Sir...")

if prompt:
    # 1. Display and Save User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
              (USER_ID, "user", prompt, datetime.now()))
    conn.commit()

    # 2. Generate and Save AI Response
    with st.chat_message("assistant"):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            with st.spinner("Analyzing data streams..."):
                response = model.generate_content(prompt)
                full_response = response.text
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
                      (USER_ID, "assistant", full_response, datetime.now()))
            conn.commit()

            # 3. Audio Protocol (British Accent)
            audio_text = full_response[:250].replace(' ', '%20').replace('"', '')
            voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={audio_text}&tl=en-gb&client=tw-ob"
            st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)
            
        except Exception as e:
            st.error(f"Core Logic Error: {e}")
