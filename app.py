import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
import time
from PIL import Image
from datetime import datetime

# --- 1. DATABASE ARCHIVE SYSTEM ---
def init_db():
    conn = sqlite3.connect('jarvis_vault.db', check_same_thread=False)
    c = conn.cursor()
    # Table for User Credentials
    c.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT)')
    # Table for Chat History
    c.execute('CREATE TABLE IF NOT EXISTS history(username TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="JARVIS Persistent Hub", layout="wide", page_icon="🤖")

st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #06121e; border-right: 1px solid #00d4ff33; }
    [data-testid="stChatMessage"] { border-radius: 15px; border: 1px solid #00d4ff22; background-color: #0a192f66; }
    h1 { text-shadow: 0 0 15px #00d4ff; font-weight: 200; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PERSISTENT LOGIN SYSTEM ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = None

def login_ui():
    st.markdown("<h1>SYSTEM ACCESS REQUIRED</h1>", unsafe_allow_html=True)
    menu = ["Login", "Register New User"]
    choice = st.selectbox("Protocol", menu)

    if choice == "Login":
        user = st.text_input("Username")
        raw_password = st.text_input("Password", type='password')
        if st.button("Authenticate"):
            c.execute('SELECT password FROM users WHERE username =?', (user,))
            data = c.fetchone()
            if data and check_hashes(raw_password, data[0]):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.success(f"Welcome back, Sir.")
                st.rerun()
            else:
                st.error("Invalid Credentials.")

    elif choice == "Register New User":
        new_user = st.text_input("Create Username")
        new_password = st.text_input("Create Password", type='password')
        if st.button("Register"):
            try:
                c.execute('INSERT INTO users(username, password) VALUES (?,?)', (new_user, make_hashes(new_password)))
                conn.commit()
                st.success("User Profile Created. You may now login.")
            except:
                st.error("Username already exists.")

if not st.session_state.logged_in:
    login_ui()
else:
    # --- 4. LOAD PERSISTENT CHAT HISTORY ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Pull history from DB
        c.execute('SELECT role, content FROM history WHERE username=? ORDER BY timestamp ASC', (st.session_state.username,))
        rows = c.fetchall()
        for row in rows:
            st.session_state.messages.append({"role": row[0], "content": row[1]})

    # --- SIDEBAR (Archive & Management) ---
    with st.sidebar:
        st.markdown(f"### 🛡️ USER: {st.session_state.username.upper()}")
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        if st.button("🗑️ PURGE ALL HISTORY"):
            c.execute('DELETE FROM history WHERE username=?', (st.session_state.username,))
            conn.commit()
            st.session_state.messages = []
            st.rerun()

    st.markdown("<h1>JARVIS INTELLIGENCE HUB</h1>", unsafe_allow_html=True)

    # Display History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- 5. THE INPUT CONSOLE ---
    st.markdown("---")
    col_menu, col_input = st.columns([0.1, 0.9])
    with col_menu:
        if st.button("⋮"):
            st.session_state.show_menu = not st.session_state.get('show_menu', False)
            st.rerun()

    # (Simplified sensor logic for storage - can re-add full menu here)
    prompt = st.chat_input("Direct JARVIS...")

    if prompt:
        # Save User Message to DB
        c.execute('INSERT INTO history(username, role, content, timestamp) VALUES (?,?,?,?)', 
                  (st.session_state.username, "user", prompt, datetime.now()))
        conn.commit()
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # Save AI Response to DB
            c.execute('INSERT INTO history(username, role, content, timestamp) VALUES (?,?,?,?)', 
                      (st.session_state.username, "assistant", response.text, datetime.now()))
            conn.commit()
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Voice Output
            voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={response.text[:250].replace(' ', '%20')}&tl=en-gb&client=tw-ob"
            st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)
            
            st.rerun()
