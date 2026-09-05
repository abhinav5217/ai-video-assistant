import os

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"

EMBEDDING_MODEL = "text-embedding-3-small"


def get_embeddings():
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=os.getenv("OPENAI_API_KEY")
    )


def build_vector_store(transcript: str) -> Chroma:

    print("Building vector store...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_text(transcript)

    docs = [
        Document(
            page_content=chunk,
            metadata={"chunk_index": i}
        )
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR
    )

    print(f"Vector store created with {len(docs)} chunks.")

    return vector_store


def load_vector_store() -> Chroma:

    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )

    return vector_store


def get_retriever(vector_store: Chroma, k: int = 4):

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )