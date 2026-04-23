import streamlit as st
import google.generativeai as genai
import time
from PIL import Image
import io

# --- 1. PRO UI SETTINGS (STARK HUB EDITION) ---
st.set_page_config(page_title="JARVIS Hub", layout="wide", page_icon="🤖")

# Custom CSS for the "ChatGPT-style but Iron Man" look
st.markdown("""
    <style>
    .stApp {
        background-color: #050a0f;
        color: #00d4ff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar Chat History Style */
    [data-testid="stSidebar"] {
        background-color: #06121e;
        border-right: 1px solid #00d4ff33;
    }
    
    /* Clean Message Bubbles */
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        border: 1px solid #00d4ff22;
        margin-bottom: 15px;
        background-color: #0a192f66;
    }

    /* Floating Input Bar Styling */
    .stChatInputContainer {
        border-top: 1px solid #00d4ff33;
        padding-top: 20px;
    }

    /* Iron Man Glow Buttons */
    .stButton>button {
        width: 100%;
        background-color: #0a192f;
        color: #00d4ff;
        border: 1px solid #00d4ff;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px #00d4ff;
        background-color: #00d4ff;
        color: #050a0f;
    }

    h1 {
        text-shadow: 0 0 15px #00d4ff;
        font-weight: 200;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "temp_storage" not in st.session_state:
    st.session_state.temp_storage = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- 3. AUTHENTICATION ---
def check_password():
    if not st.session_state.authenticated:
        st.title("SYSTEM LOCKED")
        cols = st.columns([1,2,1])
        with cols[1]:
            password = st.text_input("ENTER ACCESS CODE", type="password")
            if "ACCESS_CODE" in st.secrets and password == st.secrets["ACCESS_CODE"]:
                st.session_state.authenticated = True
                st.rerun()
        return False
    return True

if check_password():
    # --- SIDEBAR: HISTORY & STORAGE ---
    with st.sidebar:
        st.markdown("### 🕒 CHAT ARCHIVE")
        if st.button("+ NEW SESSION"):
            st.session_state.messages = []
            st.session_state.temp_storage = []
            st.rerun()
        
        st.markdown("---")
        # Show recent history
        for msg in st.session_state.messages[-6:]:
            if msg["role"] == "user":
                st.caption(f"💬 {msg['content'][:35]}...")

        st.markdown("---")
        # STORAGE VAULT
        with st.expander("📂 STORAGE (Vault)"):
            if not st.session_state.temp_storage:
                st.write("Vault empty.")
            for item in st.session_state.temp_storage:
                st.caption(f"✔️ {item['name']} ({item['type']})")
            if st.button("Purge Vault"):
                st.session_state.temp_storage = []
                st.rerun()

    st.markdown("<h1>JARVIS INTELLIGENCE HUB</h1>", unsafe_allow_html=True)

    # Display Conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- 4. INTEGRATED CHATGPT-STYLE INPUT ---
    # We use a container to group the icons and the input bar
    with st.container():
        st.markdown("---")
        # Icon row for attachments
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            uploaded_files = st.file_uploader("📎", accept_multiple_files=True, label_visibility="collapsed")
        with col2:
            cam_image = st.camera_input("📸", label_visibility="collapsed")
        with col3:
            audio_cmd = st.audio_input("🎤", label_visibility="collapsed")
        with col4:
            st.caption("Sensors Active")

        # The Text Area (Main Command)
        prompt = st.chat_input("Direct JARVIS...")

    # --- 5. MULTIMODAL LOGIC & ERROR FIX ---
    if prompt or uploaded_files or cam_image or audio_cmd:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="You are JARVIS. Professional, helpful, and high-tech. Address the user as Sir."
        )

        payload = []
        
        # 1. Add Text
        if prompt:
            payload.append(prompt)
        else:
            payload.append("Analyzing provided sensory data, Sir.")

        # 2. Add Files/Images (Fixed processing)
        if uploaded_files:
            for f in uploaded_files:
                st.session_state.temp_storage.append({"name": f.name, "type": f.type})
                if f.type.startswith("image/"):
                    payload.append(Image.open(f))
                else:
                    # PDF and other docs
                    payload.append({"mime_type": f.type, "data": f.getvalue()})

        # 3. Add Camera
        if cam_image:
            img = Image.open(cam_image)
            payload.append(img)
            st.session_state.temp_storage.append({"name": "Live_Scan.png", "type": "image/png"})

        # 4. Add Audio (FIXED: Converting UploadedFile to Gemini Blob)
        if audio_cmd:
            audio_blob = {
                "mime_type": "audio/wav",
                "data": audio_cmd.getvalue()
            }
            payload.append(audio_blob)
            st.session_state.temp_storage.append({"name": "Voice_Command.wav", "type": "audio/wav"})

        # Update History & Respond
        st.session_state.messages.append({"role": "user", "content": prompt if prompt else "Sensory Input Sent."})
        
        with st.chat_message("assistant"):
            resp_placeholder = st.empty()
            full_resp = ""
            
            try:
                response = model.generate_content(payload)
                
                # Typing Animation
                for chunk in response.text.split():
                    full_resp += chunk + " "
                    time.sleep(0.04)
                    resp_placeholder.markdown(full_resp + "▌")
                
                # Final clean text + Voice Output
                resp_placeholder.markdown(full_resp)
                st.text_to_speech(full_resp)
                
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
                st.rerun()
                
            except Exception as e:
                st.error(f"Hardware Error: {str(e)}")
