# --- 6. NEURAL EXECUTION (CORRECTED TYPES) ---
prompt = st.chat_input("Direct me, Sir...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # CORRECTED: Using 'ToolCodeExecution' and 'GoogleSearch'
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[
                    types.Tool(google_search=types.GoogleSearch()),
                    types.Tool(code_execution=types.ToolCodeExecution()) # Updated here
                ],
                temperature=0.1 # Lower temperature for better algorithmic accuracy
            )

            with st.spinner("Executing internal logic gates..."):
                # Ensure the model is set to the 2026 production build
                response = client.models.generate_content(
                    model='gemini-2.0-flash-lite', 
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
