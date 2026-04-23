import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
import base64

# --- 1. PRO UI SETTINGS ---
st.set_page_config(page_title="JARVIS Hub", layout="wide", page_icon="🤖")

st.markdown("""
    <style>
    .stApp { background-color: #050a0f; color: #00d4ff; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #06121e; border-right: 1px solid #00d4ff33; }
    
    /* Input Bar Alignment */
    .stChatInputContainer { padding-bottom: 20px; }
    
    /* Message Bubbles */
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        border: 1px solid #00d4ff22;
        background-color: #0a192f66;
    }

    /* Small Icon Buttons in Menu */
    .stButton > button {
        border: 1px solid #00d4ff;
        background-color: transparent;
        color: #00d4ff;
        border-radius: 10px;
    }
    
    .stButton > button:hover {
        background-color: #00d4ff;
        color: #050a0f;
        box-shadow: 0 0 15px #00d4ff;
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
    # --- SIDEBAR (Archive & Storage) ---
    with st.sidebar:
        st.markdown("### 🕒 CHAT ARCHIVE")
        if st.button("+ NEW SESSION"):
            st.session_state.messages = []
            st.session_state.temp_storage = []
            st.rerun()
        
        st.markdown("---")
        with st.expander("📂 STORAGE VAULT"):
            if not st.session_state.temp_storage:
                st.write("Vault empty.")
            for item in st.session_state.temp_storage:
                st.caption(f"✔️ {item['name']}")
            if st.button("Purge Vault"):
                st.session_state.temp_storage = []
                st.rerun()

    st.markdown("<h1>JARVIS INTELLIGENCE HUB</h1>", unsafe_allow_html=True)

    # Display Conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- 4. THE STEALTH INPUT CONSOLE ---
    st.markdown("---")
    
    # Bottom Bar Layout
    col_menu, col_input = st.columns([0.1, 0.9])
    
    with col_menu:
        # The ⋮ (Three Dots) Button
        if st.button("⋮", help="Open Sensors"):
            st.session_state.show_menu = not st.session_state.show_menu
            st.rerun()

    # The Collapsible Sensor Menu
    active_payload = []
    if st.session_state.show_menu:
        # Move icons inside the menu
        m1, m2, m3, m4, m_space = st.columns([1,1,1,1,6])
        with m1:
            if st.button("📎", help="Attach Files"): st.session_state.sensor_mode = "files"; st.rerun()
        with m2:
            if st.button("📸", help="Open Camera"): st.session_state.sensor_mode = "camera"; st.rerun()
        with m3:
            if st.button("🎤", help="Record Voice"): st.session_state.sensor_mode = "voice"; st.rerun()
        with m4:
            # The X (Kill Switch)
            if st.button("❌", help="Reset All Sensors"):
                st.session_state.sensor_mode = None
                st.session_state.show_menu = False
                st.rerun()

    # --- 5. SENSOR ACTIVATION LOGIC ---
    if st.session_state.sensor_mode == "files":
        uploaded_files = st.file_uploader("Upload Data (PDF/Img/Folder)", accept_multiple_files=True)
        if uploaded_files:
            for f in uploaded_files:
                st.session_state.temp_storage.append({"name": f.name})
                if f.type.startswith("image/"):
                    active_payload.append(Image.open(f))
                else:
                    active_payload.append({"mime_type": f.type, "data": f.getvalue()})

    elif st.session_state.sensor_mode == "camera":
        cam_input = st.camera_input("Optical Array Active")
        if cam_input:
            active_payload.append(Image.open(cam_input))
            st.session_state.temp_storage.append({"name": "Camera_Scan.png"})

    elif st.session_state.sensor_mode == "voice":
        audio_input = st.audio_input("Listening for Command...")
        if audio_input:
            active_payload.append({"mime_type": "audio/wav", "data": audio_input.getvalue()})
            st.session_state.temp_storage.append({"name": "Acoustic_Log.wav"})

    # Main Command Box
    prompt = st.chat_input("Direct JARVIS...")

    # --- 6. JARVIS CORE PROCESSING ---
    if prompt or active_payload:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="You are JARVIS. Respond in a sophisticated British tone. Address the user as Sir. Keep it tech-focused."
        )

        st.session_state.messages.append({"role": "user", "content": prompt if prompt else "Scanning sensory inputs..."})
        
        with st.chat_message("assistant"):
            full_resp = ""
            resp_area = st.empty()
            
            try:
                # Bundle text and binary data
                input_bundle = [prompt] if prompt else ["Analyze the provided data, Sir."]
                input_bundle.extend(active_payload)
                
                response = model.generate_content(input_bundle)
                
                # Typing Effect
                for chunk in response.text.split():
                    full_resp += chunk + " "
                    time.sleep(0.02)
                    resp_area.markdown(full_resp + "▌")
                
                resp_area.markdown(full_resp)

                # --- ACOUSTIC OUTPUT (BRITISH ACCENT) ---
                clean_text = full_resp.replace('"', '').replace("'", "").strip()[:250]
                voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={clean_text}&tl=en-gb&client=tw-ob"
                
                # Hidden Audio Bridge for Autoplay
                st.components.v1.html(f"""
                    <audio autoplay>
                        <source src="{voice_url}" type="audio/mp3">
                    </audio>
                """, height=0)
                
                # Add to history
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
                
                # Auto-reset sensors after processing
                st.session_state.sensor_mode = None
                st.session_state.show_menu = False
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"Hardware Error: {str(e)}")
