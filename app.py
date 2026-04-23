import streamlit as st
import google.generativeai as genai
import sqlite3
import time
from datetime import datetime

# --- 1. THE ARCHITECTURAL BRAIN ---
st.set_page_config(page_title="JARVIS v12.2", page_icon="🛡️", layout="wide")

# Permanent hard-coded training instructions
SYSTEM_INSTRUCTION = """
You are JARVIS, an elite AI for Sir Admin.
CORE PROTOCOLS:
1. SEARCH: Use Google Search for real-time data, news, and live updates.
2. MATH/ALGO: Use Code Execution for all math, physics, and algorithm testing.
3. PERSONA: Sophisticated, British, and proactive. Always address the user as 'Sir'.
"""

# Retrieve secrets
try:
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except:
    st.error("CRITICAL ERROR: Credentials missing in Streamlit Secrets.")
    st.stop()

# --- 2. STORAGE ARCHIVE ---
def init_db():
    conn = sqlite3.connect('jarvis_v12_2.db', check_same_thread=False)
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
            else:
                st.error("ACCESS DENIED: Internal Security Triggered.")
    st.stop()

# --- 4. SIDEBAR STATUS ---
with st.sidebar:
    st.title("🛡️ JARVIS OS")
    st.status("Core: Gemini 2.5 Flash-Lite", state="complete")
    st.write("✅ Google Search Active")
    st.write("✅ Code Execution Active")
    
    if st.button("Purge Local Memory"):
        c.execute('DELETE FROM history WHERE user_id=?', (USER_ID,))
        conn.commit()
        st.session_state.messages = []
        st.rerun()

# --- 5. CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    c.execute('SELECT role, content FROM history WHERE user_id=? ORDER BY timestamp ASC', (USER_ID,))
    for row in c.fetchall():
        st.session_state.messages.append({"role": row[0], "content": row[1]})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. THE THINKING CORE (STABILITY UPGRADE) ---
prompt = st.chat_input("Direct JARVIS, Sir...")

if prompt:
    # Save & Display User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # UPDATED TOOL SYNTAX FOR 2026 SDK
            # We use the built-in string identifiers to prevent 'Unknown Field' errors
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash-lite',
                tools=['google_search', 'code_execution'],
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            with st.spinner("Analyzing global data and calculating..."):
                # Start chat with history for context-aware training
                chat = model.start_chat(history=[
                    {"role": m["role"].replace("assistant", "model"), "parts": [m["content"]]} 
                    for m in st.session_state.messages[:-1]
                ])
                
                # Auto-Retry for Quota (429)
                for attempt in range(2):
                    try:
                        response = chat.send_message(prompt)
                        response_text = response.text
                        break
                    except Exception as e:
                        if "429" in str(e):
                            time.sleep(10)
                            continue
                        raise e

            # Render Citations and Final Response
            st.markdown(response_text)
            
            # Save to Permanent Archive
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            c.execute('INSERT INTO history(user_id, role, content, timestamp) VALUES (?,?,?,?)', 
                      (USER_ID, "assistant", response_text, datetime.now()))
            conn.commit()

            # Voice Protocol (Shortened for speed)
            audio_text = response_text[:150].replace(' ', '%20').replace('"', '')
            voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={audio_text}&tl=en-gb&client=tw-ob"
            st.components.v1.html(f'<audio autoplay src="{voice_url}"></audio>', height=0)

        except Exception as e:
            st.error(f"Logic Failure: {e}")
