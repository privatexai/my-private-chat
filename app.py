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
    .stChatInputContainer { padding-bottom: 20px; }
    
    /* Menu Icon Styling */
    .menu-btn { font-size: 24px; cursor: pointer; border: 1px solid #00d4ff; border-radius: 5px; padding: 5px; text-align: center; }
    
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

    # --- 4. STEALTH INPUT CONSOLE ---
    st.markdown("---")
    
    # Input Row
    col_menu, col_input = st.columns([0.1, 0.9])
    
    with col_menu:
        if st.button("⋮", help="Toggle Sensors"):
            st.session_state.show_menu = not st.session_state.show_menu
            st.rerun()

    # Collapsible Sensor Menu
    if st.session_state.show_menu:
        m1, m2, m3, m4, m5 = st.columns([1,1,1,1,6])
        with m1: 
            if st.button("📎"): st.session_state.sensor_mode = "files"; st.rerun()
        with m2: 
            if st.button("📸"): st.session_state.sensor_mode = "camera"; st.rerun()
        with m3: 
            if st.button("🎤"): st.session_state.sensor_mode = "voice"; st.rerun()
        with m4:
            if st.button("❌", help="Close Sensors"):
                st.session_state.sensor_mode = None
                st.session_state.show_menu = False
                st.rerun()

    # Active Sensor Logic
    active_payload = []
    if st.session_state.sensor_mode == "files":
        files = st.file_uploader("Upload", accept_multiple_files=True)
        if files:
            for f in files:
                st.session_state.temp_storage.append({"name": f.name})
                active_payload.append(Image.open(f) if f.type.startswith("image/") else {"mime_type": f.type, "data": f.getvalue()})
    
    elif st.session_state.sensor_mode == "camera":
        cam = st.camera_input("Optical Sensor Active")
        if cam:
            active_payload.append(Image.open(cam))
            st.session_state.temp_storage.append({"name": "Camera_Capture.png"})
            
    elif st.session_state.sensor_mode == "voice":
        voice = st.audio_input("Listening...")
        if voice:
            active_payload.append({"mime_type": "audio/wav", "data": voice.getvalue()})
            st.session_state.temp_storage.append({"name": "Voice_Log.wav"})

    prompt = st.chat_input("Direct JARVIS...")

    # --- 5. EXECUTION (BRITISH PROTOCOL) ---
    if prompt or active_payload:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        input_list = [prompt] if prompt else ["Sir, I am scanning the provided data now."]
        input_list.extend(active_payload)

        st.session_state.messages.append({"role": "user", "content": prompt if prompt else "Sensory scan initiated."})
        
        with st.chat_message("assistant"):
            full_resp = ""
            resp_area = st.empty()
            try:
                response = model.generate_content(input_list)
                
                # Typing effect
                for chunk in response.text.split():
                    full_resp += chunk + " "
                    time.sleep(0.02)
                    resp_area.markdown(full_resp + "▌")
                
                resp_area.markdown(full_resp)
                
                # --- NEW: HIGH-QUALITY UK VOICE ---
                # We use an encoded URL for a professional British Male voice
                # 'tl=en-gb' forces the UK accent
                encoded_text = full_resp.replace(" ", "%20")[:300] # Limit length for speed
                voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl=en-gb&client=tw-ob"
                
                st.audio(voice_url, format="audio/mp3", autoplay=True)
                
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
                
                # Reset sensors for next command
                st.session_state.sensor_mode = None
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Acoustic Error: {str(e)}")
