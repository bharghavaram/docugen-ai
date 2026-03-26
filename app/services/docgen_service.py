"""
DocuGen AI – Document Generation & Summarisation using LlamaIndex + ChromaDB.
"""
import logging
import os
from pathlib import Path
from typing import Optional, List

import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings as LISettings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.mistralai import MistralAI
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer

from app.core.config import settings

logger = logging.getLogger(__name__)

DOCUMENT_TEMPLATES = {
    "executive_summary": """Generate a concise executive summary (max 500 words) that includes:
- Key findings and insights
- Critical metrics and data points
- Strategic recommendations
- Risk factors

Base this on the provided source documents.""",

    "technical_report": """Generate a detailed technical report with:
1. Abstract
2. Introduction and background
3. Methodology / approach
4. Results and analysis
5. Discussion
6. Conclusions
7. References (cite from source documents)

Maintain technical precision and cite evidence from the documents.""",

    "business_proposal": """Generate a professional business proposal including:
- Executive Overview
- Problem Statement
- Proposed Solution
- Implementation Plan
- Timeline and Milestones
- Budget Estimate
- Expected ROI
- Risk Assessment

Tailor to business decision-makers.""",

    "meeting_notes": """Generate structured meeting notes including:
- Meeting summary
- Key discussion points
- Decisions made
- Action items (with owners and deadlines)
- Next steps

Format clearly for distribution.""",
}


class DocGenService:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )
        self.collection = self.chroma_client.get_or_create_collection("docugen")

        self.llm_claude = Anthropic(
            model=settings.CLAUDE_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
        )
        self.llm_mistral = MistralAI(
            model=settings.MISTRAL_MODEL,
            api_key=settings.MISTRAL_API_KEY,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
        )
        self.index: Optional[VectorStoreIndex] = None
        self._load_index()

    def _load_index(self):
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        LISettings.llm = self.llm_claude
        if self.collection.count() > 0:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store, storage_context=storage_context
            )
            logger.info("Loaded existing ChromaDB index with %d vectors", self.collection.count())

    def ingest_documents(self, file_paths: List[str]) -> dict:
        from llama_index.core.node_parser import SentenceSplitter
        docs_path = Path(settings.DOCUMENTS_PATH)
        docs_path.mkdir(parents=True, exist_ok=True)

        reader = SimpleDirectoryReader(input_files=file_paths)
        documents = reader.load_data()

        splitter = SentenceSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        LISettings.llm = self.llm_claude

        if self.index is None:
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                transformations=[splitter],
            )
        else:
            for doc in documents:
                self.index.insert(doc)

        return {
            "documents_ingested": len(documents),
            "total_vectors": self.collection.count(),
        }

    def generate_document(
        self,
        query: str,
        doc_type: str = "executive_summary",
        llm_provider: str = "claude",
    ) -> dict:
        if self.index is None:
            return {
                "document": "No documents indexed. Please upload source documents first.",
                "doc_type": doc_type,
                "llm_provider": llm_provider,
            }

        template = DOCUMENT_TEMPLATES.get(doc_type, DOCUMENT_TEMPLATES["executive_summary"])
        full_query = f"{template}\n\nSpecific focus: {query}"

        llm = self.llm_claude if llm_provider == "claude" else self.llm_mistral
        LISettings.llm = llm

        retriever = VectorIndexRetriever(index=self.index, similarity_top_k=8)
        synthesizer = get_response_synthesizer(response_mode="tree_summarize", llm=llm)
        engine = RetrieverQueryEngine(retriever=retriever, response_synthesizer=synthesizer)

        response = engine.query(full_query)
        sources = [
            {
                "source": node.metadata.get("file_name", "unknown"),
                "score": round(node.score, 3) if node.score else None,
            }
            for node in response.source_nodes
        ]

        return {
            "document": str(response),
            "doc_type": doc_type,
            "llm_provider": llm_provider,
            "sources_used": sources,
        }

    def summarise(self, text: str, style: str = "concise") -> dict:
        styles = {
            "concise": "Summarise in 3-5 bullet points:",
            "detailed": "Provide a comprehensive summary with sections:",
            "executive": "Write a one-paragraph executive summary:",
        }
        prompt = f"{styles.get(style, styles['concise'])}\n\n{text}"
        response = self.llm_claude.complete(prompt)
        return {"summary": response.text, "style": style}

    def get_stats(self) -> dict:
        return {
            "total_indexed_chunks": self.collection.count(),
            "chroma_persist_dir": settings.CHROMA_PERSIST_DIR,
            "available_templates": list(DOCUMENT_TEMPLATES.keys()),
        }


_service: Optional[DocGenService] = None


def get_docgen_service() -> DocGenService:
    global _service
    if _service is None:
        _service = DocGenService()
    return _service
