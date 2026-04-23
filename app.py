import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
import time
from datetime import datetime
from PIL import Image

# --- 1. THE ARCHIVE ENGINE (SQLite) ---
def init_db():
    conn = sqlite3.connect('jarvis_vault.db', check_same_thread=False)
    c = conn.cursor()
    # Users table: Stores email/mobile and hashed password
    c.execute('CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, password TEXT, type TEXT)')
    # History table: Linked by user_id
    c.execute('CREATE TABLE IF NOT EXISTS history(user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. UI & SECURITY CONFIG ---
st.set_page_config(page_title="JARVIS Double-Lock Hub", layout="wide")

# Set your Master Passcode here (Tier 1)
MASTER_PASSCODE = "STARK2026" 

st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; }
    [data-testid="stSidebar"] { background-color: #06121e; border-right: 1px solid #00d4ff33; }
    .stChatInputContainer { padding-bottom: 20px; }
    h1 { text-shadow: 0 0 15px #00d4ff; text-align: center; font-weight: 200; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TIER 1: GLOBAL GATEKEEPER ---
if "gate_passed" not in st.session_state: st.session_state.gate_passed = False

if not st.session_state.gate_passed:
    st.markdown("<h1>REMOTELY ENCRYPTED TERMINAL</h1>", unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        passcode = st.text_input("ENTER MASTER PASSCODE", type="password")
        if st.button("Unlock Gate"):
            if passcode == MASTER_PASSCODE:
                st.session_state.gate_passed = True
                st.rerun()
            else:
                st.error("ACCESS DENIED: Internal Security Triggered.")
    st.stop()

# --- 4. TIER 2: PERSONAL VAULT LOGIN ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_id" not in st.session_state: st.session_state.user_id = None

def login_system():
    st.markdown("<h1>USER IDENTIFICATION</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        u_id = st.text_input("Email or Mobile Number")
        u_pw = st.text_input("User Password", type="password", key="login_pw")
        if st.button("Access Vault"):
            c.execute('SELECT password FROM users WHERE id=?', (u_id,))
            result = c.fetchone()
            if result and result[0] == hash_pass(u_pw):
                st.session_state.logged_in = True
                st.session_state.user_id = u_id
                st.rerun()
            else:
                st.error("Identity verification failed.")

    with tab2:
        new_id = st.text_input("Register Email/Mobile")
        new_pw = st.text_input("Create Password", type="password", key="reg_pw")
        if st.button("Create Profile"):
            try:
                c.execute('INSERT INTO users(id, password) VALUES (?,?)', (new_id, hash_pass(new_pw)))
                conn.commit()
                st.success("Profile initialized. Switch to Login tab.")
            except:
                st.error("ID already registered in the database.")

if not st.session_state.logged_in:
    login_system()
    st.stop()

# --- 5. JARVIS INTERFACE (LOAD USER DATA) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Fetch only THIS user's history
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (st.session_state.user_id,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

# SIDEBAR
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_id}")
    if st.button("LOGOUT"):
        st.session_state.logged_in = False
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    if st.button("🗑️ PURGE MY VAULT"):
        c.execute('DELETE FROM history WHERE user_id=?', (st.session_state.user_id,))
        conn.commit()
        st.session_state.messages = []
        st.rerun()

st.markdown(f"<h1>JARVIS HUB: {st.session_state.user_id}</h1>", unsafe_allow_html=True)

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# Input Logic
prompt = st.chat_input("Enter command, Sir...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
              (st.session_state.user_id, "user", prompt, datetime.now()))
    conn.commit()
    
    with st.chat_message("assistant"):
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
                  (st.session_state.user_id, "assistant", response.text, datetime.now()))
        conn.commit()
        
        # Audio Output
        voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={response.text[:200].replace(' ', '%20')}&tl=en-gb&client=tw-ob"
        st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)
        st.rerun()
