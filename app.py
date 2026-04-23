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
    /* Main Background */
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
    
    /* Input Area Container */
    .stChatInputContainer {
        padding-bottom: 20px;
    }

    /* Message Styling */
    [data-testid="stChatMessage"] {
        border-radius: 10px;
        border: 1px solid #00d4ff22;
        margin-bottom: 15px;
    }
    
    /* Custom Sidebar Buttons */
    .stButton>button {
        width: 100%;
        background-color: #0a192f;
        color: #00d4ff;
        border: 1px solid #00d4ff;
        border-radius: 5px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px #00d4ff;
        background-color: #00d4ff;
        color: #050a0f;
    }

    h1 {
        text-shadow: 0 0 15px #00d4ff;
        font-weight: 200;
        letter-spacing: 3px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE INITIALIZATION ---
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
    # --- SIDEBAR: CHAT HISTORY & STORAGE ---
    with st.sidebar:
        st.markdown("### 🕒 CHAT ARCHIVE")
        if st.button("+ NEW SESSION"):
            st.session_state.messages = []
            st.session_state.temp_storage = []
            st.rerun()
        
        st.markdown("---")
        # Display snippets of chat history
        for idx, msg in enumerate(st.session_state.messages[-5:]):
            if msg["role"] == "user":
                st.caption(f"Q: {msg['content'][:30]}...")

        st.markdown("---")
        # STORAGE BUTTON
        with st.expander("📦 STORAGE (Temp Data)"):
            if not st.session_state.temp_storage:
                st.write("Vault empty.")
            for item in st.session_state.temp_storage:
                st.caption(f"✅ {item['name']}")
            if st.button("Purge Vault"):
                st.session_state.temp_storage = []
                st.rerun()

    # --- MAIN UI ---
    st.markdown("<h1>JARVIS INTELLIGENCE HUB</h1>", unsafe_allow_html=True)

    # Display Conversation
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # --- THE "CHATGPT" INPUT CONSOLE ---
    st.markdown("---")
    
    # Sensory Input Row (Right above text box)
    input_cols = st.columns([2, 2, 2, 4])
    
    with input_cols[0]:
        uploaded_files = st.file_uploader("📎 FILES", accept_multiple_files=True, label_visibility="collapsed")
    with input_cols[1]:
        cam_image = st.camera_input("📸 SCAN", label_visibility="collapsed")
    with input_cols[2]:
        audio_cmd = st.audio_input("🎤 VOICE", label_visibility="collapsed")

    # The Main Text Input
    prompt = st.chat_input("Direct JARVIS...")

    # --- 4. DATA PROCESSING ---
    if prompt or uploaded_files or cam_image or audio_cmd:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="You are JARVIS. Use a ChatGPT-style helpfulness with a high-tech Iron Man personality. Address the user as Sir."
        )

        # Prepare the payload
        payload = []
        
        if prompt:
            payload.append(prompt)
        
        # Process multiple files (PDF, Images, etc.)
        if uploaded_files:
            for f in uploaded_files:
                st.session_state.temp_storage.append({"name": f.name, "type": f.type})
                if f.type.startswith("image/"):
                    payload.append(Image.open(f))
                else:
                    # For PDFs/Docs, Gemini reads bytes
                    payload.append({"mime_type": f.type, "data": f.getvalue()})

        if cam_image:
            img = Image.open(cam_image)
            payload.append(img)
            st.session_state.temp_storage.append({"name": "Camera_Capture.png", "type": "image/png"})

        if audio_cmd:
            payload.append(audio_cmd)
            st.session_state.temp_storage.append({"name": "Voice_Note.wav", "type": "audio/wav"})

        # Update History
        user_text = prompt if prompt else "Analyzing sensory data..."
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        # Trigger JARVIS
        with st.chat_message("assistant"):
            resp_placeholder = st.empty()
            full_resp = ""
            
            try:
                response = model.generate_content(payload)
                
                # Typing effect + Acoustic response
                for chunk in response.text.split():
                    full_resp += chunk + " "
                    time.sleep(0.04)
                    resp_placeholder.markdown(full_resp + "▌")
                
                # Native Voice Output (Optional: only if you want it to speak every time)
                st.text_to_speech(response.text)
                
                resp_placeholder.markdown(full_resp)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
                st.rerun() # Refresh to update sidebar history
                
            except Exception as e:
                st.error(f"Hardware Error: {str(e)}")
