import streamlit as st
import google.generativeai as genai
import time

# --- 1. PRO UI SETTINGS (JARVIS STYLE) ---
st.set_page_config(page_title="JARVIS Terminal", layout="wide")

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
    .stTextInput input {
        background-color: #0a192f;
        color: #00d4ff;
        border: 1px solid #00d4ff;
    }
    h1 {
        text-shadow: 0 0 20px #00d4ff;
        text-align: center;
        letter-spacing: 5px;
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
        if password == st.secrets["ACCESS_CODE"]:
            st.session_state.authenticated = True
            st.rerun()
        return False
    return True

if check_password():
    st.markdown("<h1>JARVIS PROTOCOL ACTIVE</h1>", unsafe_allow_html=True)

    # --- 3. CONFIGURE GEMINI ---
    # Replace with your actual API Key
   genai.configure(api_key=st.secrets["GEMINI_KEY"])
    
    # SYSTEM INSTRUCTION: Tells Gemini how to behave
    model = genai.GenerativeModel(
      model_name='gemini-3.1-flash-preview',
        system_instruction="You are JARVIS, the highly intelligent AI assistant from Iron Man. Be polite, concise, and professional. Address the user as 'Sir'. Use tech terms occasionally."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("awaiting orders..."):
        # Display User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate JARVIS Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Add a small "loading" animation
                with st.spinner("Analyzing data..."):
                    response = model.generate_content(prompt)
                
                # Typing effect
                for chunk in response.text.split():
                    full_response += chunk + " "
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"System Error: {str(e)}")
