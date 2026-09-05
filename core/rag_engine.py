import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableLambda,
)

from core.vector_store import (
    build_vector_store,
    get_retriever,
)


load_dotenv()


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
# LLM
# ============================================================

def get_llm():

    api_key = get_api_key()

    if not api_key:

        raise ValueError(
            "OPENAI_API_KEY not found. "
            "Add it to Streamlit Secrets or your .env file."
        )

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=api_key,
    )


# ============================================================
# FORMAT DOCUMENTS
# ============================================================

def format_docs(docs):

    if not docs:
        return "No relevant transcript context found."

    return "\n\n".join(
        doc.page_content
        for doc in docs
    )


# ============================================================
# RAG PROMPT
# ============================================================

def get_rag_prompt():

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an expert meeting assistant.

Answer the user's question based ONLY on the
meeting transcript context provided below.

If the answer is not found in the context,
say exactly:

"I could not find this information in the meeting transcript."

Rules:

- Do not invent information.
- Do not use outside knowledge.
- Be concise and precise.
- If quoting someone, mention it clearly.
- Use only the provided transcript context.

Context from meeting transcript:

{context}
                """,
            ),
            (
                "human",
                "{question}",
            ),
        ]
    )


# ============================================================
# BUILD RAG CHAIN
# ============================================================

def build_rag_chain(transcript: str):

    if not transcript:

        raise ValueError(
            "Transcript is empty. "
            "Cannot build RAG system."
        )

    print(
        "Building RAG chain..."
    )

    # --------------------------------------------------------
    # Build vector store
    # --------------------------------------------------------

    vector_store = build_vector_store(
        transcript
    )

    # --------------------------------------------------------
    # Retriever
    # --------------------------------------------------------

    retriever = get_retriever(
        vector_store,
        k=4,
    )

    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    llm = get_llm()

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = get_rag_prompt()

    # --------------------------------------------------------
    # LCEL RAG pipeline
    # --------------------------------------------------------

    rag_chain = (
        {
            "context": (
                retriever
                | RunnableLambda(format_docs)
            ),

            "question": RunnablePassthrough(),
        }

        | prompt

        | llm

        | StrOutputParser()
    )

    print(
        "RAG chain created successfully."
    )

    return rag_chain


# ============================================================
# ASK QUESTION
# ============================================================

def ask_question(
    rag_chain,
    question: str
) -> str:

    if not question:

        return (
            "Please enter a question."
        )

    print(
        f"Question: {question}"
    )

    answer = rag_chain.invoke(
        question
    )

    print(
        f"Answer: {answer}"
    )

    return answer