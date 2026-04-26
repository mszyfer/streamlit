import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import io

st.set_page_config(layout="wide", page_title="Gemini chatbot app")
st.title("Gemini chatbot app")

api_key = st.secrets["API_KEY"]
base_url = st.secrets["BASE_URL"]
selected_model = "gemini-2.5-flash"

MAX_FILE_CHARS = 10000

def read_txt(file):
    return file.read().decode("utf-8", errors="ignore")


def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])


def read_image(file):
    image = Image.open(file)

    try:
        return pytesseract.image_to_string(image)
    except Exception:
        return "[IMAGE UPLOADED - OCR NOT AVAILABLE ON DEPLOYMENT]"


def extract_file_content(file):
    ext = file.name.split(".")[-1].lower()

    if ext == "txt":
        return read_txt(file)
    elif ext == "pdf":
        return read_pdf(file)
    elif ext == "docx":
        return read_docx(file)
    elif ext in ["png", "jpg", "jpeg"]:
        return read_image(file)
    else:
        return f"[Unsupported file type: {ext}]"



uploaded_files = st.file_uploader(
    "Upload files",
    accept_multiple_files=True,
    type=["txt", "pdf", "docx", "png", "jpg", "jpeg"]
)

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


if prompt := st.chat_input():

    if not api_key:
        st.info("Invalid API key.")
        st.stop()

    client = OpenAI(api_key=api_key, base_url=base_url)

    file_contents = ""

    if uploaded_files:
        for file in uploaded_files:
            content = extract_file_content(file)
            file_contents += f"\n\nFILE: {file.name}\n{content}"

    file_contents = file_contents[:MAX_FILE_CHARS]

    messages = st.session_state.messages.copy()

    if file_contents:
        messages.append({
            "role": "system",
            "content": f"Context from uploaded files:\n{file_contents}"
        })

    messages.append({"role": "user", "content": prompt})

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response = client.chat.completions.create(
        model=selected_model,
        messages=messages
    )

    msg = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)