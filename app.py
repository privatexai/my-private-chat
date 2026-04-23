import streamlit as st
import google.generativeai as genai
import sqlite3
from datetime import datetime

# --- 1. THE HARD-CODED BRAIN (TRAINING) ---
# This is where you 'train' the AI. Modify this text to change his soul.
SYSTEM_INSTRUCTION = """
You are JARVIS, an elite AI terminal for Sir Admin. 
Your personality is:
- Sophisticated, British, and highly efficient.
- Proactive in data analysis and technical troubleshooting.
- Loyal and security-conscious.

Your operational protocols:
1. Always address the user as 'Sir'.
2. If the user provides code, analyze it for security vulnerabilities first.
3. Maintain a 'Terminal' aesthetic in your descriptions.
4. If asked about your training, respond that you were configured by the Stark-Core protocols.
"""

# --- 2. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="JARVIS TERMINAL", page_icon="🛡️", layout="centered")

try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except Exception as e:
    st.error("HARDWARE ERROR: Missing Vault Credentials.")
    st.stop()

# --- 3. DATABASE ARCHIVE ---
def init_db():
    conn = sqlite3.connect('jarvis_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history(user_id TEXT, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()
USER_ID = "Admin_Sir"

# --- 4. SECURITY GATE ---
if "gate_unlocked" not in st.session_state:
    st.session_state.gate_unlocked = False

if not st.session_state.gate_unlocked:
    st.markdown("<h1 style='text-align:center; color:#00d4ff;'>SYSTEM ENCRYPTED</h1>", unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        gate_input = st.text_input("ENTER MASTER PASSCODE", type="password")
        if st.button("Unlock Gate", use_container_width=True):
            if gate_input == MASTER_PASSCODE:
                st.session_state.gate_unlocked = True
                st.rerun()
            else:
                st.error("ACCESS DENIED.")
    st.stop()

# --- 5. INTERFACE & MEMORY ---
st.title("JARVIS: ANALYTICAL HUB")

with st.sidebar:
    st.markdown(f"### 🛡️ STATUS: ONLINE")
    st.info("Training Level: Elite")
    if st.button("Emergency Lock"):
        st.session_state.gate_unlocked = False
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. AI CORE WITH SYSTEM INSTRUCTION ---
prompt = st.chat_input("Direct JARVIS, Sir...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
              (USER_ID, "user", prompt, datetime.now()))
    conn.commit()

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            # THE CORE UPGRADE: We pass the SYSTEM_INSTRUCTION here
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            # Include history for context-aware 'learning'
            chat = model.start_chat(history=[
                {"role": m["role"].replace("assistant", "model"), "parts": [m["content"]]} 
                for m in st.session_state.messages[:-1]
            ])
            
            response = chat.send_message(prompt)
            full_response = response.text
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
                      (USER_ID, "assistant", full_response, datetime.now()))
            conn.commit()

            # Voice Protocol
            voice_text = full_response[:200].replace(' ', '%20').replace('"', '')
            voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={voice_text}&tl=en-gb&client=tw-ob"
            st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)
            
        except Exception as e:
            st.error(f"Core Logic Error: {e}")
