import os
import uuid

from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_core.documents import Document


load_dotenv()


# ============================================================
# CONFIG
# ============================================================

COLLECTION_NAME_PREFIX = (
    "meeting_transcript"
)

EMBEDDING_MODEL = (
    "text-embedding-3-small"
)


# ============================================================
# API KEY
# ============================================================

def get_api_key():
    """
    API key ko:
    1. Streamlit Secrets
    2. .env / Environment Variable

    se read karta hai.
    """

    try:

        import streamlit as st

        if "OPENAI_API_KEY" in st.secrets:

            return st.secrets[
                "OPENAI_API_KEY"
            ]

    except Exception:
        pass

    return os.getenv(
        "OPENAI_API_KEY"
    )


# ============================================================
# EMBEDDINGS
# ============================================================

def get_embeddings():

    api_key = get_api_key()

    if not api_key:

        raise ValueError(
            "OPENAI_API_KEY not found. "
            "Add it to Streamlit Secrets or your .env file."
        )

    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=api_key,
    )


# ============================================================
# BUILD VECTOR STORE
# ============================================================

def build_vector_store(
    transcript: str
) -> Chroma:

    if not transcript:

        raise ValueError(
            "Transcript is empty. "
            "Cannot create vector store."
        )

    print(
        "Building vector store..."
    )

    # --------------------------------------------------------
    # Split transcript
    # --------------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(
        transcript
    )

    if not chunks:

        raise ValueError(
            "No transcript chunks were created."
        )

    # --------------------------------------------------------
    # Create documents
    # --------------------------------------------------------

    docs = [

        Document(
            page_content=chunk,
            metadata={
                "chunk_index": i
            },
        )

        for i, chunk in enumerate(chunks)
    ]

    # --------------------------------------------------------
    # Embeddings
    # --------------------------------------------------------

    embeddings = get_embeddings()

    # --------------------------------------------------------
    # Unique collection
    #
    # Important:
    # Har video ke liye different collection
    # create hoga.
    # --------------------------------------------------------

    unique_collection_name = (
        f"{COLLECTION_NAME_PREFIX}_"
        f"{uuid.uuid4().hex[:12]}"
    )

    # --------------------------------------------------------
    # In-memory Chroma
    #
    # Streamlit Cloud compatible.
    # No persistent local database required.
    # --------------------------------------------------------

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=unique_collection_name,
    )

    print(
        f"Vector store created with "
        f"{len(docs)} chunks."
    )

    return vector_store


# ============================================================
# RETRIEVER
# ============================================================

def get_retriever(
    vector_store: Chroma,
    k: int = 4,
):

    if vector_store is None:

        raise ValueError(
            "Vector store is not available."
        )

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k
        },
    )