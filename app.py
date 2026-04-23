import streamlit as st
import sqlite3
import time
from datetime import datetime
from google import genai
from google.genai import types

# --- 1. SYSTEM ARCHITECTURE ---
st.set_page_config(page_title="JARVIS v13.0", page_icon="🛡️", layout="wide")

# Iron Man Terminal Styling
st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; font-family: 'Courier New', Courier, monospace; }
    .stChatMessage { border-radius: 10px; border: 1px solid #00d4ff; margin-bottom: 10px; background-color: #0a192f; }
    .stButton>button { background-color: #00d4ff; color: black; border-radius: 5px; width: 100%; }
    .stTextInput>div>div>input { background-color: #0a192f; color: #00d4ff; border: 1px solid #00d4ff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION & CORE INITIALIZATION ---
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    MASTER_PASSCODE = st.secrets["ACCESS_CODE"]
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"CRITICAL: Hardware Authentication Failed. {e}")
    st.stop()

# --- 3. DATABASE ARCHIVE ---
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
                st.error("ACCESS DENIED: Protocol 11-A Triggered.")
    st.stop()

# --- 5. INTERFACE TABS ---
tab_chat, tab_veo = st.tabs(["🧠 Intelligence Core", "🎥 Cinematic Lab"])

# --- 6. INTELLIGENCE CORE (Text, Math, Search) ---
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
                # 2026 Multimodal Intelligence Config
                config = types.GenerateContentConfig(
                    system_instruction="You are JARVIS. Use Search for news and Code for math. Address user as Sir.",
                    tools=[
                        types.Tool(google_search=types.GoogleSearch()),
                        types.Tool(code_execution=types.ToolCodeExecution())
                    ],
                    temperature=0.2
                )

                with st.spinner("Analyzing data streams..."):
                    # Using gemini-2.0-flash to bypass the -lite quota exhaustion
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

# --- 7. CINEMATIC LAB (Veo 3.1) ---
with tab_veo:
    st.subheader("Veo 3.1 Visual Generation")
    video_prompt = st.text_area("Describe the cinematic visual, Sir (e.g., 'A futuristic London skyline with flying cars at sunset')")
    
    if st.button("Engage Render Engine"):
        if video_prompt:
            try:
                with st.spinner("JARVIS is rendering the visual sequence (approx 90s)..."):
                    operation = client.models.generate_videos(
                        model="veo-2", # Updated for the 2026 Veo-series name
                        prompt=video_prompt,
                        config=types.GenerateVideosConfig(
                            aspect_ratio="16:9",
                            video_format="mp4"
                        )
                    )
                    
                    # Polling for completion
                    while not operation.done:
                        time.sleep(10)
                        operation = client.operations.get(operation.name)
                    
                    video_url = operation.result.generated_videos[0].video.path
                    st.video(video_url)
                    st.success("Visual stream stabilized, Sir.")
            except Exception as e:
                st.error(f"Render Failure: {e}")
        else:
            st.warning("Please provide a prompt for the rendering engine, Sir.")
