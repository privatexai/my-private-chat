import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
import io

# --- 1. PRO UI SETTINGS ---
st.set_page_config(page_title="JARVIS Hub", layout="wide", page_icon="🤖")

st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #06121e; border-right: 1px solid #00d4ff33; }
    
    /* Input Bar Container */
    .stChatInputContainer { padding-bottom: 20px; }
    
    /* Glowing X Button */
    .kill-button button {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 50% !important;
        border: none !important;
        box-shadow: 0 0 10px #ff4b4b;
    }
    
    /* Message bubbles */
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        border: 1px solid #00d4ff22;
        background-color: #0a192f66;
    }
    h1 { text-shadow: 0 0 15px #00d4ff; font-weight: 200; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "temp_storage" not in st.session_state: st.session_state.temp_storage = []
if "authenticated" not in st.session_state: st.session_state.authenticated = False
# UI Toggles
if "show_menu" not in st.session_state: st.session_state.show_menu = False
if "sensor_mode" not in st.session_state: st.session_state.sensor_mode = None

# --- 3. AUTHENTICATION ---
def check_password():
    if not st.session_state.authenticated:
        st.title("SYSTEM LOCKED")
        password = st.text_input("ENTER ACCESS CODE", type="password")
        if "ACCESS_CODE" in st.secrets and password == st.secrets["ACCESS_CODE"]:
            st.session_state.authenticated = True
            st.rerun()
        return False
    return True

if check_password():
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### 🕒 CHAT ARCHIVE")
        if st.button("+ NEW SESSION"):
            st.session_state.messages = []; st.session_state.temp_storage = []; st.rerun()
        
        st.markdown("---")
        with st.expander("📂 STORAGE"):
            for item in st.session_state.temp_storage: st.caption(f"✔️ {item['name']}")

    st.markdown("<h1>JARVIS INTELLIGENCE HUB</h1>", unsafe_allow_html=True)

    # Display Chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    # --- 4. THE STEALTH INPUT CONSOLE ---
    st.markdown("---")
    
    # Control Row
    ctrl_col1, ctrl_col2 = st.columns([0.1, 0.9])
    
    with ctrl_col1:
        if st.button("⋮"):
            st.session_state.show_menu = not st.session_state.show_menu

    # The Collapsible Menu
    if st.session_state.show_menu:
        menu_cols = st.columns([1, 1, 1, 1, 6])
        with menu_cols[0]:
            if st.button("📎"): st.session_state.sensor_mode = "files"
        with menu_cols[1]:
            if st.button("📸"): st.session_state.sensor_mode = "camera"
        with menu_cols[2]:
            if st.button("🎤"): st.session_state.sensor_mode = "voice"
        with menu_cols[3]:
            st.markdown('<div class="kill-button">', unsafe_allow_html=True)
            if st.button("X"): 
                st.session_state.sensor_mode = None
                st.session_state.show_menu = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Active Sensor Display
    active_files, active_cam, active_voice = None, None, None
    
    if st.session_state.sensor_mode == "files":
        active_files = st.file_uploader("Upload Data", accept_multiple_files=True)
    elif st.session_state.sensor_mode == "camera":
        active_cam = st.camera_input("Optical Sensor Active")
    elif st.session_state.sensor_mode == "voice":
        active_voice = st.audio_input("Listening...")

    # Main Command Bar
    prompt = st.chat_input("Direct JARVIS...")

    # --- 5. LOGIC ---
    if prompt or active_files or active_cam or active_voice:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
        payload = []
        
        if prompt: payload.append(prompt)
        if active_files:
            for f in active_files:
                payload.append(Image.open(f) if f.type.startswith("image/") else {"mime_type": f.type, "data": f.getvalue()})
                st.session_state.temp_storage.append({"name": f.name})
        if active_cam:
            payload.append(Image.open(active_cam))
            st.session_state.temp_storage.append({"name": "Camera_Capture.png"})
        if active_voice:
            payload.append({"mime_type": "audio/wav", "data": active_voice.getvalue()})
            st.session_state.temp_storage.append({"name": "Voice_Log.wav"})

        # Response
        st.session_state.messages.append({"role": "user", "content": prompt if prompt else "Input processed."})
        with st.chat_message("assistant"):
            full_resp = ""
            resp_area = st.empty()
            response = model.generate_content(payload)
            for chunk in response.text.split():
                full_resp += chunk + " "
                time.sleep(0.03)
                resp_area.markdown(full_resp + "▌")
            resp_area.markdown(full_resp)
            st.text_to_speech(full_resp)
            st.session_state.messages.append({"role": "assistant", "content": full_resp})
            # Reset sensors after sending
            st.session_state.sensor_mode = None
            st.rerun()
