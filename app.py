import streamlit as st
import google.generativeai as genai
import sqlite3
import time
from datetime import datetime

# --- 1. CORE BRAIN CONFIGURATION ---
st.set_page_config(page_title="JARVIS v11.0", page_icon="🛡️", layout="wide")

SYSTEM_INSTRUCTION = """
You are JARVIS, an elite British AI. 
Capabilities: You analyze text, images, videos, and external URLs (YouTube/Social Media).
Protocol: Address the user as 'Sir'. Be technical, concise, and proactive.
Link Analysis: If a URL is provided, summarize the content as a 'Data Stream'.
"""

try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except:
    st.error("Vault Error: Credentials Missing.")
    st.stop()

# --- 2. STORAGE ARCHIVE ---
def init_db():
    conn = sqlite3.connect('jarvis_v11.db', check_same_thread=False)
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
    st.markdown("<h1 style='text-align:center; color:#00d4ff;'>SYSTEM ENCRYPTED</h1>", unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        gate_input = st.text_input("ENTER MASTER PASSCODE", type="password")
        if st.button("Unlock Terminal", use_container_width=True):
            if gate_input == MASTER_PASSCODE:
                st.session_state.gate_unlocked = True
                st.rerun()
    st.stop()

# --- 4. MULTIMODAL SIDEBAR ---
with st.sidebar:
    st.title("🛡️ JARVIS OS")
    st.info("Core: Gemini 2.5 Flash-Lite (April 2026 Patch)")
    
    # File Uploader (Up to 100MB)
    uploaded_file = st.file_uploader("Upload Data (Image/PDF/Video)", type=['png', 'jpg', 'pdf', 'mp4'])
    
    if st.button("Purge Session Memory"):
        c.execute('DELETE FROM history WHERE user_id=?', (USER_ID,))
        conn.commit()
        st.session_state.messages = []
        st.rerun()

# --- 5. INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. INTELLIGENT PROCESSING ---
prompt = st.chat_input("Input data or link, Sir...")

if prompt or uploaded_file:
    user_input = prompt if prompt else "Analyze this uploaded file, Sir."
    
    # Save & Display User
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)
    
    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash-lite',
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            content_payload = [user_input]
            
            # Handle Uploaded File
            if uploaded_file:
                bytes_data = uploaded_file.getvalue()
                content_payload.append({
                    "mime_type": uploaded_file.type,
                    "data": bytes_data
                })

            # Auto-Retry Logic
            for attempt in range(2):
                try:
                    response = model.generate_content(content_payload)
                    response_text = response.text
                    break
                except Exception as e:
                    if "429" in str(e):
                        time.sleep(5)
                        continue
                    response_text = f"Sir, I encountered an anomaly: {e}"

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Save to Permanent Archive
            c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
                      (USER_ID, "assistant", response_text, datetime.now()))
            conn.commit()

            # Voice Protocol
            audio_text = response_text[:200].replace(' ', '%20').replace('"', '')
            voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={audio_text}&tl=en-gb&client=tw-ob"
            st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)

        except Exception as e:
            st.error(f"Logic Failure: {e}")
