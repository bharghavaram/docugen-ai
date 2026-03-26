"""DocuGen AI – Streamlit frontend."""
import streamlit as st
import httpx

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="DocuGen AI", page_icon="📄", layout="wide")
st.title("📄 DocuGen AI – Intelligent Document Generation")
st.markdown("Generate structured documents from your unstructured data using Claude & Mistral.")

tab1, tab2, tab3 = st.tabs(["📤 Upload Documents", "✍️ Generate Document", "📝 Summarise Text"])

with tab1:
    st.header("Upload Source Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF or text documents", accept_multiple_files=True, type=["pdf", "txt", "md"]
    )
    if st.button("Ingest Documents") and uploaded_files:
        with st.spinner("Ingesting documents into ChromaDB..."):
            files = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files]
            try:
                r = httpx.post(f"{API_URL}/documents/upload", files=files, timeout=120)
                result = r.json()
                st.success(f"✅ Ingested {result.get('documents_ingested', 0)} documents, {result.get('total_vectors', 0)} chunks indexed.")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.header("Generate Document")
    query = st.text_area("What document do you need?", placeholder="Generate a sustainability report for Q3 2024...")
    col1, col2 = st.columns(2)
    with col1:
        doc_type = st.selectbox("Document Type", ["executive_summary", "technical_report", "business_proposal", "meeting_notes"])
    with col2:
        llm_provider = st.selectbox("LLM Provider", ["claude", "mistral"])

    if st.button("🚀 Generate") and query:
        with st.spinner(f"Generating {doc_type} using {llm_provider}..."):
            try:
                r = httpx.post(
                    f"{API_URL}/documents/generate",
                    json={"query": query, "doc_type": doc_type, "llm_provider": llm_provider},
                    timeout=120,
                )
                result = r.json()
                st.markdown("### Generated Document")
                st.markdown(result.get("document", ""))
                if result.get("sources_used"):
                    st.markdown("#### Sources Used")
                    for src in result["sources_used"]:
                        st.caption(f"📄 {src['source']} (score: {src['score']})")
            except Exception as e:
                st.error(f"Error: {e}")

with tab3:
    st.header("Text Summarisation")
    text = st.text_area("Paste text to summarise", height=200)
    style = st.radio("Summary Style", ["concise", "detailed", "executive"], horizontal=True)
    if st.button("Summarise") and text:
        with st.spinner("Summarising..."):
            try:
                r = httpx.post(f"{API_URL}/documents/summarise", json={"text": text, "style": style}, timeout=60)
                st.markdown("### Summary")
                st.write(r.json().get("summary", ""))
            except Exception as e:
                st.error(f"Error: {e}")
