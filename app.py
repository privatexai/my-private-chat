import streamlit as st
import google.generativeai as genai
import sqlite3
import time
from datetime import datetime

# --- 1. THE GATEKEEPER ---
# Pulls the secret 'ACCESS_CODE' from your Streamlit Vault
try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
except:
    st.error("Hardware Error: ACCESS_CODE not found in Vault.")
    st.stop()

if "gate_unlocked" not in st.session_state:
    st.session_state.gate_unlocked = False

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

# --- 2. AUTOMATIC USER SYNC (GOOGLE) ---
# Once the gate is open, we identify the user via Google for history tracking
if not st.user.is_logged_in:
    st.markdown("<h1 style='text-align:center;'>IDENTIFYING OPERATOR...</h1>", unsafe_allow_html=True)
    st.button("Sign in with Google", on_click=st.login, type="primary", use_container_width=True)
    st.stop()

# --- 3. PERSISTENT DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('jarvis_vault.db', check_same_thread=False)
    c = conn.cursor()
    # We only need the history table now, linked to Google Email
    c.execute('CREATE TABLE IF NOT EXISTS history(user_email TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()

# --- 4. SECURE USER INTERFACE ---
st.title(f"JARVIS HUB: {st.user.name.upper()}")

# Sidebar for logout and system info
with st.sidebar:
    st.image(st.user.picture, width=100)
    st.write(f"Operator: {st.user.email}")
    if st.button("Secure Logout"):
        st.session_state.gate_unlocked = False
        st.logout()

# Load Chat History for THIS Google Account
if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_email=? ORDER BY timestamp ASC', (st.user.email,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

# Display Conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. ANALYTICAL CORE ---
prompt = st.chat_input("Direct JARVIS...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    c.execute('INSERT INTO history(user_email, role, content, timestamp) VALUES (?,?,?,?)', 
              (st.user.email, "user", prompt, datetime.now()))
    conn.commit()
    
    with st.chat_message("assistant"):
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content(prompt)
        
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        c.execute('INSERT INTO history(user_email, role, content, timestamp) VALUES (?,?,?,?)', 
                  (st.user.email, "assistant", response.text, datetime.now()))
        conn.commit()
        
        # Acoustic Protocol (British Voice)
        voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={response.text[:200].replace(' ', '%20')}&tl=en-gb&client=tw-ob"
        st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)
