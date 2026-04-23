import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# --- 1. GATEKEEPER CONFIG ---
# This pulls the 'Master Pass' from your Streamlit Secrets Vault
try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
except:
    st.error("Hardware Error: ACCESS_CODE not found in Vault.")
    st.stop()

# --- 2. PERSONAL DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('jarvis_vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history(user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 3. TIER 1: THE GLOBAL PASSCODE GATE ---
if "gate_unlocked" not in st.session_state: st.session_state.gate_unlocked = False

if not st.session_state.gate_unlocked:
    st.markdown("<h1 style='text-align:center;'>SYSTEM ENCRYPTED</h1>", unsafe_allow_html=True)
    gate_input = st.text_input("ENTER MASTER PASSCODE", type="password")
    if st.button("Unlock Terminal"):
        if gate_input == MASTER_PASSCODE:
            st.session_state.gate_unlocked = True
            st.rerun()
        else:
            st.error("Invalid Master Passcode.")
    st.stop()

# --- 4. TIER 2: PERSONAL LOGIN (Email/Mobile) ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_id" not in st.session_state: st.session_state.user_id = None

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>USER IDENTIFICATION</h1>", unsafe_allow_html=True)
    mode = st.radio("Protocol", ["Login", "Register New Profile"])
    
    u_id = st.text_input("Email or Mobile Number")
    u_pw = st.text_input("Private Password", type="password")
    
    if mode == "Login":
        if st.button("Verify Identity"):
            c.execute('SELECT password FROM users WHERE id=?', (u_id,))
            res = c.fetchone()
            if res and res[0] == hash_pass(u_pw):
                st.session_state.logged_in = True
                st.session_state.user_id = u_id
                st.rerun()
            else:
                st.error("Access Denied: Identity mismatch.")
    else:
        if st.button("Initialize Profile"):
            try:
                c.execute('INSERT INTO users(id, password) VALUES (?,?)', (u_id, hash_pass(u_pw)))
                conn.commit()
                st.success("Profile Created. Please switch to Login.")
            except:
                st.error("This ID is already registered.")
    st.stop()

# --- 5. SECURE USER HUB ---
st.title(f"JARVIS HUB: {st.session_state.user_id}")

# From here, all queries use: WHERE user_id = st.session_state.user_id
# This keeps your storage completely separate from any other user.
