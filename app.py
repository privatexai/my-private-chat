import streamlit as st
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="JARVIS v10", page_icon="🛡️", layout="wide")

# Classic Terminal Styling
st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; font-family: 'Courier New', Courier, monospace; }
    .stChatMessage { border-radius: 10px; border: 1px solid #00d4ff; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION & LEGACY SETUP ---
try:
    # Reverting to legacy configuration method
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    
    # Initializing the 1.5 Flash model (High Stability)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction="You are JARVIS, an elite British AI. Address the user as Sir. Focus on efficiency and logic."
    )
except Exception as e:
    st.error(f"Hardware Error: {e}")
    st.stop()

# --- 3. DATABASE ARCHIVE ---
def init_db():
    conn = sqlite3.connect('jarvis_v10.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history(role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()

# --- 4. SECURITY GATE ---
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if not st.session_state.unlocked:
    st.markdown("<h1 style='text-align:center;'>SYSTEM ENCRYPTED</h1>", unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        gate_input = st.text_input("ENTER PASSCODE", type="password")
        if st.button("Unlock Terminal"):
            if gate_input == MASTER_PASSCODE:
                st.session_state.unlocked = True
                st.rerun()
            else:
                st.error("ACCESS DENIED.")
    st.stop()

# --- 5. CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Load history from DB
    c.execute('SELECT role, content FROM history ORDER BY timestamp ASC')
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. LOGIC EXECUTION ---
prompt = st.chat_input("Direct me, Sir...")

if prompt:
    # Display user input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process Assistant Response
    with st.chat_message("assistant"):
        try:
            # We use a standard chat session for v10 stability
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]} 
                for m in st.session_state.messages[:-1]
            ])
            
            with st.spinner("Processing..."):
                response = chat.send_message(prompt)
                response_text = response.text

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Save to Database
            c.execute('INSERT INTO history(role, content, timestamp) VALUES (?,?,?)', 
                      ("assistant", response_text, datetime.now()))
            conn.commit()

        except Exception as e:
            if "429" in str(e):
                st.error("Sir, even the legacy core is exhausted. Please wait 60 seconds for the quota to reset.")
            else:
                st.error(f"Logic Failure: {e}")
