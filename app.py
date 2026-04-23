import streamlit as st
import google.generativeai as genai
import time
from PIL import Image

# --- 1. PRO UI SETTINGS (JARVIS STYLE) ---
st.set_page_config(page_title="JARVIS Terminal", layout="wide", page_icon="🤖")

# Custom CSS for the "Iron Man" look
st.markdown("""
    <style>
    .stApp {
        background-color: #050a0f;
        color: #00d4ff;
        font-family: 'Courier New', Courier, monospace;
    }
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #00d4ff;
        box-shadow: 0 0 10px #00d4ff33;
    }
    /* Chat on Right (User) */
    [data-testid="stChatMessage"]:nth-child(even) {
        flex-direction: row-reverse !important;
        background-color: #0a192f;
        text-align: right;
        margin-left: 20%;
    }
    /* AI on Left (JARVIS) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #06121e;
        margin-right: 20%;
    }
    .stTextInput input, .stChatInput input {
        background-color: #0a192f !important;
        color: #00d4ff !important;
        border: 1px solid #00d4ff !important;
    }
    h1 {
        text-shadow: 0 0 20px #00d4ff;
        text-align: center;
        letter-spacing: 5px;
    }
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #050a0f;
        border-right: 1px solid #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("SYSTEM LOCKED")
        password = st.text_input("ENTER ACCESS CODE", type="password")
        if "ACCESS_CODE" in st.secrets and password == st.secrets["ACCESS_CODE"]:
            st.session_state.authenticated = True
            st.rerun()
        elif password != "":
            st.error("ACCESS DENIED")
        return False
    return True

if check_password():
    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.title("🛰️ SENSORS")
        # VISION: Image Upload
        uploaded_file = st.file_uploader("UPLOAD VISUAL DATA", type=['png', 'jpg', 'jpeg'])
        
        # VOICE: Audio Input (2026 Native Feature)
        audio_data = st.audio_input("VOICE COMMAND")
        
        st.markdown("---")
        if st.button("CLEAR ARCHIVE"):
            st.session_state.messages = []
            st.rerun()

    st.markdown("<h1>JARVIS PROTOCOL ACTIVE</h1>", unsafe_allow_html=True)

    # --- 3. CONFIGURE GEMINI ---
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction="You are JARVIS, the highly intelligent AI assistant from Iron Man. Be polite, concise, and professional. Address the user as 'Sir'. Use tech terms like 'Scanning', 'Analyzing', 'Protocols' frequently."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input Handling
    prompt = st.chat_input("awaiting orders...")
    
    # Trigger if there is a Text prompt, an Image, or Audio
    if prompt or uploaded_file or audio_data:
        # Use audio as prompt if text is empty
        input_data = []
        display_text = prompt if prompt else "Analyzing sensory input..."
        
        if prompt:
            input_data.append(prompt)
        
        if uploaded_file:
            img = Image.open(uploaded_file)
            input_data.append(img)
            st.sidebar.image(img, caption="Visual Data Received")

        if audio_data:
            # Note: In 2026, Gemini 2.5 processes st.audio_input directly
            input_data.append(audio_data)

        # Display User message
        st.session_state.messages.append({"role": "user", "content": display_text})
        with st.chat_message("user"):
            st.markdown(display_text)

        # Generate JARVIS Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                with st.spinner("Processing sensory streams..."):
                    response = model.generate_content(input_data)
                
                # Typing effect animation
                for chunk in response.text.split():
                    full_response += chunk + " "
                    time.sleep(0.04)
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"System Error: {str(e)}")
