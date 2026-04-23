import streamlit as st
import google.generativeai as genai
import sqlite3
from datetime import datetime

# --- 1. GATEKEEPER CONFIG ---
try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
except:
    st.error("Hardware Error: ACCESS_CODE not found in Vault.")
    st.stop()

# --- 2. AUTHENTICATION STATE ---
if "gate_unlocked" not in st.session_state:
    st.session_state.gate_unlocked = False

# --- 3. THE PASSCODE GATE ---
if not st.session_state.gate_unlocked:
    st.markdown("<h1 style='text-align:center; color:#00d4ff;'>SYSTEM ENCRYPTED</h1>", unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        gate_input = st.text_input("ENTER MASTER PASSCODE", type="password")
        if st.button("Unlock Terminal", use_container_width=True):
            if gate_input == MASTER_PASSCODE:
                st.session_state.gate_unlocked = True
                st.rerun()
            else:
                st.error("Access Denied: Invalid Passcode.")
    st.stop()

# --- 4. SECURE USER HUB (Single User Mode) ---
# Since we removed Google, we'll use a fixed ID for your local storage
USER_ID = "Admin_Sir" 

def init_db():
    conn = sqlite3.connect('jarvis_vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history(user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()

st.title("JARVIS SECURE TERMINAL")

# Sidebar for logout
with st.sidebar:
    st.markdown("### 🛡️ STATUS: SECURE")
    if st.button("Lock Terminal"):
        st.session_state.gate_unlocked = False
        st.rerun()

# Load History
if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. ANALYTICAL CORE ---
prompt = st.chat_input("Direct JARVIS...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
              (USER_ID, "user", prompt, datetime.now()))
    conn.commit()
    
    with st.chat_message("assistant"):
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
                  (USER_ID, "assistant", response.text, datetime.now()))
        conn.commit()
        
        # Audio Synthesis
        voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={response.text[:200].replace(' ', '%20')}&tl=en-gb&client=tw-ob"
        st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)
