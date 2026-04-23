import streamlit as st
import google.generativeai as genai

# 1. Setup Password Protection
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        password = st.text_input("Enter Passcode", type="password")
        if password == "1234": # Set your common passcode here
            st.session_state.authenticated = True
            st.rerun()
        return False
    return True

if check_password():
    # 2. Configure Gemini
    genai.configure(api_key="AIzaSyDNIuMYxSegF3pRrZBnQIqmWND4w-uX5vk")
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    st.title("My Private AI")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What is on your mind?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
