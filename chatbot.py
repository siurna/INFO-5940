"""
Streamlit-based RAG application
LangChain + Chroma + Cornell AI Gateway
Author: Tomas Šiurna
"""

# --- Standard library ---
import os
import json
from pypdf import PdfReader

# --- Third-party libraries ---
import streamlit as st
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# =============================================================================
# GLOBAL SETTINGS
# =============================================================================
BASE_URL = "https://api.ai.it.cornell.edu/v1"
CHAT_MODEL = "openai.gpt-4o-mini"
EMBED_MODEL = "openai.text-embedding-3-small"
CHUNK_SIZE = 1000

HISTORY_FILE = "data/chat_history.json"
SUMMARY_CACHE = "data/summaries.json"
os.makedirs("data", exist_ok=True)

# =============================================================================
# STREAMLIT SETUP
# =============================================================================
st.set_page_config(page_title="Tomas Šiurna Document Chat", page_icon="💡", layout="centered")

# --- Load external CSS ---
def local_css(file_name: str):
    """Injects local CSS into Streamlit app."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ CSS file '{file_name}' not found. Using default style.")

local_css("special_sauce.css")

st.title("💬 The most helpful RAG")

# =============================================================================
# API KEY INPUT
# =============================================================================
if "api_ready" not in st.session_state:
    st.session_state.api_ready = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if not st.session_state.api_ready:
    st.markdown("### 🔐 Enter your API Key to Start")
    key_input = st.text_input("Cornell AI Gateway API Key", type="password")
    if key_input:
        st.session_state.api_key = key_input.strip()
        st.session_state.api_ready = True
        st.success("✅ API key loaded successfully! You can now upload documents.")
        st.rerun()

if not st.session_state.api_ready:
    st.stop()

client = OpenAI(api_key=st.session_state.api_key, base_url=BASE_URL)

# =============================================================================
# HELPERS
# =============================================================================

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def extract_text(file):
    if file.name.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")
    elif file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        st.error("Unsupported file type.")
        return ""

def build_vectorstore(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=0)
    docs = splitter.create_documents([text])
    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL,
        openai_api_base=BASE_URL,
        openai_api_key=st.session_state.api_key
    )
    return Chroma.from_documents(docs, embedding=embeddings)

def generate_chat_response(prompt, context=""):
    """Flexible RAG call using Cornell Gateway."""
    if context:
        system = (
            "You are a helpful assistant. Use the provided context as your primary reference, "
            "but you may also infer or generalize when relevant. Avoid saying 'not found' unless clearly absent.\n\n"
            f"Context:\n{context}\n\n"
        )
    else:
        system = "You are an assistant that writes concise and accurate summaries."

    try:
        resp = client.responses.create(
            model=CHAT_MODEL,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.output[0].content[0].text.strip()
    except Exception as e:
        return f"Error: {e}"

# =============================================================================
# STATE INIT
# =============================================================================
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "history" not in st.session_state:
    st.session_state.history = load_json(HISTORY_FILE, [])
summaries = load_json(SUMMARY_CACHE, {})

# =============================================================================
# SIDEBAR
# =============================================================================
st.sidebar.header("📁 Upload Documents")

uploaded_files = st.sidebar.file_uploader("", type=["txt", "pdf"], accept_multiple_files=True)

# Push clear button to bottom of sidebar
st.sidebar.markdown("<div style='flex-grow:1;'></div>", unsafe_allow_html=True)
if st.sidebar.button("🧹 Clear Chat History", use_container_width=True):
    st.session_state.history = []
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    st.sidebar.success("History cleared!")

# =============================================================================
# DOCUMENT HANDLING
# =============================================================================
if uploaded_files:
    file_keys = [f"{f.name}_{f.size}" for f in uploaded_files]
    cache_key = "_".join(file_keys)

    with st.spinner("Processing documents..."):
        all_text = "\n\n".join(extract_text(f) for f in uploaded_files)
        st.session_state.vector_store = build_vectorstore(all_text)
    st.sidebar.success(f"Indexed {len(uploaded_files)} document(s).")

    # Cached summary
    if cache_key in summaries:
        summary_text = summaries[cache_key]
    else:
        summary_prompt = f"Summarize this document briefly:\n\n{all_text[:4000]}"
        with st.spinner("Generating document summary..."):
            summary_text = generate_chat_response(summary_prompt)
            summaries[cache_key] = summary_text
            save_json(SUMMARY_CACHE, summaries)

    st.info("📝 **Document Summary**\n\n" + summary_text)

# =============================================================================
# MAIN CHAT
# =============================================================================
if st.session_state.vector_store is None:
    st.info("👈 Upload one or more documents to begin.")
else:
    # Display chat history
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask about your documents...")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 4})
        docs = retriever.get_relevant_documents(user_input)
        context = "\n\n".join(d.page_content[:500] for d in docs)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = generate_chat_response(user_input, context)
                st.markdown(answer)

        st.session_state.history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": answer},
        ])
        save_json(HISTORY_FILE, st.session_state.history)