import streamlit as st
from openai import OpenAI

st.set_page_config(layout="wide", page_title="Gemini chatbot app")
st.title("Gemini chatbot app")

api_key, base_url = st.secrets["API_KEY"], st.secrets["BASE_URL"]
selected_model = "gemini-2.5-flash"

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if st.session_state.uploaded_files:
    st.markdown("**Uploaded files:**")
    for f in st.session_state.uploaded_files:
        st.write(f"📄 {f.name}")

col1, col2 = st.columns([1, 10])

with col1:
    new_files = st.file_uploader(
        "➕",
        label_visibility="collapsed",
        accept_multiple_files=True,
        type=["txt"]
    )

    if new_files:
        st.session_state.uploaded_files.extend(new_files)

with col2:
    prompt = st.chat_input("Type your message...")

if prompt:
    if not api_key:
        st.info("Invalid API key.")
        st.stop()

    client = OpenAI(api_key=api_key, base_url=base_url)


    file_contents = ""
    for file in st.session_state.uploaded_files:
        content = file.read().decode("utf-8")
        file_contents += f"\n\nFile: {file.name}\n{content}"

    full_prompt = prompt
    if file_contents:
        full_prompt += f"\n\nHere are uploaded files:\n{file_contents}"

    st.session_state.messages.append({"role": "user", "content": full_prompt})
    st.chat_message("user").write(prompt)

    response = client.chat.completions.create(
        model=selected_model,
        messages=st.session_state.messages
    )

    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)