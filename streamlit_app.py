import streamlit as st
from openai import OpenAI

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="Gemini chatbot app")
st.title("Gemini chatbot app")

api_key = st.secrets["API_KEY"]
base_url = st.secrets["BASE_URL"]
selected_model = "gemini-2.5-flash"

MAX_FILE_CHARS = 10000  # limit długości kontekstu z plików

# --- FILE UPLOADER ---
uploaded_files = st.file_uploader(
    "Upload files",
    accept_multiple_files=True,
    type=["txt"]
)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

# --- DISPLAY CHAT ---
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- INPUT ---
if prompt := st.chat_input():

    if not api_key:
        st.info("Invalid API key.")
        st.stop()

    client = OpenAI(api_key=api_key, base_url=base_url)

    # --- READ FILES (NOT saved to history) ---
    file_contents = ""
    if uploaded_files:
        for file in uploaded_files:
            content = file.read().decode("utf-8")
            file_contents += f"\n\nFile: {file.name}\n{content}"

    # limit size
    file_contents = file_contents[:MAX_FILE_CHARS]

    # --- BUILD MESSAGES (IMPORTANT: copy history) ---
    messages = st.session_state.messages.copy()

    # add files as context (NOT user message!)
    if file_contents:
        messages.append({
            "role": "system",
            "content": f"Context from uploaded files:\n{file_contents}"
        })

    # add current user prompt
    messages.append({
        "role": "user",
        "content": prompt
    })

    # --- DISPLAY USER MESSAGE ---
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    st.chat_message("user").write(prompt)

    # --- API CALL ---
    response = client.chat.completions.create(
        model=selected_model,
        messages=messages
    )

    msg = response.choices[0].message.content

    # --- SAVE & DISPLAY RESPONSE ---
    st.session_state.messages.append({
        "role": "assistant",
        "content": msg
    })
    st.chat_message("assistant").write(msg)