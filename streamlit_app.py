import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import numpy as np
import faiss

from langchain_huggingface import HuggingFaceEmbeddings
from embedder_rag import FAISSIndex


st.set_page_config(layout="wide", page_title="RAG chatbot app")
st.title("RAG chatbot app")


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
        return "[OCR not available]"


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



@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )



def build_index(texts, metadata, embeddings):
    vectors = [embeddings.embed_query(t) for t in texts]
    vectors = np.array(vectors).astype("float32")

    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    return FAISSIndex(index, metadata)


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


uploaded_files = st.file_uploader(
    "Upload files",
    accept_multiple_files=True,
    type=["txt", "pdf", "docx", "png", "jpg", "jpeg"]
)

if uploaded_files:
    texts = []
    metadata = []

    embeddings = get_embeddings()

    for file in uploaded_files:
        content = extract_file_content(file)

        chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]

        for chunk in chunks:
            texts.append(chunk)
            metadata.append({
                "filename": file.name,
                "text": chunk
            })

    st.session_state["faiss"] = build_index(texts, metadata, embeddings)



if prompt := st.chat_input():

    if not api_key:
        st.info("Missing API key.")
        st.stop()

    client = OpenAI(api_key=api_key, base_url=base_url)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)



    context = ""

    if "faiss" in st.session_state:
        results = st.session_state["faiss"].similarity_search(prompt, k=3)

        context = "\n\n".join(
            f"[{r['filename']}]\n{r['text']}"
            for r in results
        )


    messages = st.session_state.messages.copy()

    if context:
        messages.insert(0, {
            "role": "system",
            "content": f"Use this context to answer:\n\n{context}"
        })



    response = client.chat.completions.create(
        model=selected_model,
        messages=messages
    )

    answer = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)