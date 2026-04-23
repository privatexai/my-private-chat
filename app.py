with st.chat_message("assistant"):
            try:
                with st.spinner("Analyzing data streams..."):
                    # Attempting generation
                    response = client.models.generate_content(
                        model='gemini-2.0-flash', # Or switch to 'gemini-1.5-flash' for legacy free
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
                if "429" in str(e):
                    st.warning("⚠️ **QUOTA DEPLETED:** Sir, the reactor core requires a billing link to unlock Gemini 2.0/Veo 3.1. Please check AI Studio or switch to a legacy model.")
                else:
                    st.error(f"Logic Breach: {e}")
