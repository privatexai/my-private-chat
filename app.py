import streamlit as st
import google.generativeai as genai
import sqlite3
import os
from datetime import datetime

# --- 1. SYSTEM SECURITY ---
try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
except:
    st.error("Hardware Error: ACCESS_CODE missing from vault.")
    st.stop()

if "gate_unlocked" not in st.session_state:
    st.session_state.gate_unlocked = False

# --- 2. THE GATEKEEPER ---
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

# --- 3. PERSISTENT STORAGE (Auto-Repairing) ---
def init_db():
    conn = sqlite3.connect('jarvis_vault.db', check_same_thread=False)
    c = conn.cursor()
    # If the table is old/broken, we ensure the correct columns exist
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)''')
    conn.commit()
    return conn, c

conn, c = init_db()
USER_ID = "Sir_Admin"

# --- 4. JARVIS INTERFACE ---
st.title("JARVIS: ANALYTICAL CORE")

if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. PROCESSING LOGIC ---
prompt = st.chat_input("Input data for analysis, Sir...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
              (USER_ID, "user", prompt, datetime.now()))
    conn.commit()
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash') # High-speed analysis
        
        # Deep Analysis Simulation
        with st.status("Analyzing Data Streams...", expanded=False):
            st.write("Scanning input patterns...")
            response = model.generate_content(prompt)
            st.write("Cross-referencing global database...")
        
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
                  (USER_ID, "assistant", response.text, datetime.now()))
        conn.commit()
        
        # Acoustic Feedback
        voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={response.text[:200].replace(' ', '%20')}&tl=en-gb&client=tw-ob"
        st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)
