import streamlit as st
import sqlite3
import time
import tempfile
from datetime import datetime
from google import genai
from google.genai import types

# --- 1. CORE SYSTEM ARCHITECTURE ---
st.set_page_config(page_title="JARVIS v13.1", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; font-family: 'Courier New', Courier, monospace; }
    .stChatMessage { border-radius: 10px; border: 1px solid #00d4ff; margin-bottom: 10px; background-color: #0a192f; }
    .stButton>button { background-color: #00d4ff; color: black; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION & CLIENT ---
try:
    # This pulls directly from your Streamlit Secrets
    client = genai.Client(api_key=st.secrets["GEMINI_KEY"])
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
except Exception as e:
    st.error(f"SYSTEM FAILURE: Missing Secret Credentials. {e}")
    st.stop()

# --- 3. DATABASE PROTOCOLS ---
def init_db():
    conn = sqlite3.connect('jarvis_v13.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS history(role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    return conn, c

conn, c = init_db()

# --- 4. SECURITY GATE ---
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if not st.session_state.unlocked:
    st.markdown("<h1 style='text-align:center;'>JARVIS SECURE TERMINAL</h1>", unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        gate_input = st.text_input("ENCRYPTION KEY", type="password")
        if st.button("Decrypt Systems"):
            if gate_input == MASTER_PASSCODE:
                st.session_state.unlocked = True
                st.rerun()
            else:
                st.error("ACCESS DENIED.")
    st.stop()

# --- 5. MULTIMODAL INTERFACE ---
tab_chat, tab_veo = st.tabs(["🧠 Intelligence Core", "🎥 Cinematic Lab"])

# --- TAB 1: CHAT & LOGIC ---
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []
        c.execute('SELECT role, content FROM history ORDER BY timestamp ASC')
        for row in c.fetchall():
            st.session_state.messages.append({"role": row[0], "content": row[1]})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Direct the AI, Sir...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                # 2026 Intelligence Config
                config = types.GenerateContentConfig(
                    system_instruction="You are JARVIS. Address the user as Sir. Use Code for math/logic.",
                    tools=[
                        types.Tool(google_search=types.GoogleSearch()),
                        types.Tool(code_execution=types.ToolCodeExecution())
                    ],
                    temperature=0.1
                )

                with st.spinner("Analyzing data streams..."):
                    # Using the standard Flash core for higher quota/stability
                    response = client.models.generate_content(
                        model='gemini-2.0-flash', 
                        contents=prompt,
                        config=config
                    )
                    response_text = response.text

                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                c.execute('INSERT INTO history(role, content, timestamp) VALUES (?,?,?)', 
                          ("assistant", response_text, datetime.now()))
                conn.commit()

            except Exception as e:
                st.error(f"Logic Breach: {e}")

# --- TAB 2: VEO 3.1 CINEMATICS ---
with tab_veo:
    st.subheader("Veo 3.1 High-Fidelity Render Engine")
    video_prompt = st.text_area("Describe the cinematic scene...")
    
    if st.button("Engage Render"):
        if video_prompt:
            try:
                with st.spinner("Rendering cinematic sequence (approx 90s)..."):
                    # Initiate Veo 3.1
                    operation = client.models.generate_videos(
                        model="veo-3.1-generate-preview",
                        prompt=video_prompt,
                        config=types.GenerateVideosConfig(aspect_ratio="16:9")
                    )
                    
                    # Polling Protocol
                    while not operation.done:
                        time.sleep(10)
                        operation = client.operations.get(operation.name)
                    
                    # Process and Display
                    generated_video = operation.response.generated_videos[0]
                    
                    # Streamlit-friendly video display
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                        client.files.download(file=generated_video.video, path=tmp_file.name)
                        st.video(tmp_file.name)
                        
                    st.success("Visual stream stabilized, Sir.")
            except Exception as e:
                st.error(f"Render Failure: {e}")
        else:
            st.warning("Render prompt required, Sir.")
