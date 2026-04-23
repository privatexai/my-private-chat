import streamlit as st
import google.generativeai as genai
import sqlite3
import time
from datetime import datetime

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="JARVIS TERMINAL", page_icon="🛡️")

# Fast Cache for greetings (No API call needed)
FAST_REPLIES = {
    "hello": "Hello, Sir. Systems are nominal.",
    "status": "All systems secure. Flash-Lite core active.",
    "hi": "Ready for your next command, Sir.",
}

# Training Persona
SYSTEM_INSTRUCTION = "You are JARVIS, an elite British AI for Sir Admin. Be fast, technical, and sophisticated."

try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("Vault Error: Credentials Missing.")
    st.stop()

# --- 2. DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('jarvis_v3.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history(user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()
USER_ID = "Admin_Sir"

# --- 3. SECURITY GATE ---
if "gate_unlocked" not in st.session_state:
    st.session_state.gate_unlocked = False

if not st.session_state.gate_unlocked:
    st.markdown("<h1 style='text-align:center;'>SYSTEM ENCRYPTED</h1>", unsafe_allow_html=True)
    gate_input = st.text_input("ENTER MASTER PASSCODE", type="password")
    if st.button("Unlock Terminal"):
        if gate_input == MASTER_PASSCODE:
            st.session_state.gate_unlocked = True
            st.rerun()
    st.stop()

# --- 4. INTERFACE ---
st.title("JARVIS: FLASH CORE")

if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. PROCESSING WITH RETRY LOGIC ---
prompt = st.chat_input("Direct JARVIS...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', (USER_ID, "user", prompt, datetime.now()))
    conn.commit()

    # Instant Check
    lower_p = prompt.lower().strip()
    if lower_p in FAST_REPLIES:
        response_text = FAST_REPLIES[lower_p]
    else:
        with st.chat_message("assistant"):
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Upgraded to 2.5 Flash-Lite for higher quota
                model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash-lite', 
                    system_instruction=SYSTEM_INSTRUCTION
                )
                
                # Automatic Retry Logic for 429 Errors
                for attempt in range(3):
                    try:
                        response = model.generate_content(prompt)
                        response_text = response.text
                        break
                    except Exception as e:
                        if "429" in str(e) and attempt < 2:
                            st.warning(f"Quota spike detected. Retrying in {5 * (attempt+1)}s...")
                            time.sleep(5 * (attempt+1))
                        else:
                            response_text = f"Sir, I am encountering a rate limit. Please hold for a moment. Error: {e}"
            except Exception as e:
                response_text = f"Hardware Failure: {e}"

    st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', (USER_ID, "assistant", response_text, datetime.now()))
    conn.commit()
