import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda


load_dotenv()


def get_api_key():
    """
    API key ko:
    1. Streamlit Secrets se
    2. Environment variable / .env se
    read karega.
    """

    # Streamlit Cloud Secrets
    try:
        import streamlit as st

        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]

    except Exception:
        pass

    # Local .env / environment variable
    return os.getenv("OPENAI_API_KEY")


def get_llm():
    """
    OpenAI LLM initialize karta hai.
    """

    api_key = get_api_key()

    if not api_key:

        raise ValueError(
            "OPENAI_API_KEY not found. "
            "Add it to Streamlit Secrets or your .env file."
        )

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=api_key
    )


def split_transcript(transcript: str) -> list:
    """
    Long transcript ko smaller chunks me divide karta hai.
    """

    if not transcript:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )

    return splitter.split_text(transcript)


def summarize(transcript: str) -> str:
    """
    Complete meeting transcript ka professional summary generate karta hai.
    """

    if not transcript:
        return "No transcript available."

    llm = get_llm()

    # ---------------------------------------------------------
    # STEP 1: Transcript ko chunks me divide karo
    # ---------------------------------------------------------

    chunks = split_transcript(transcript)

    if not chunks:
        return "No transcript available."

    # ---------------------------------------------------------
    # STEP 2: Har chunk ka summary
    # ---------------------------------------------------------

    map_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Summarize this portion of a meeting transcript "
                "concisely. Focus on important information, "
                "topics, decisions, and discussion points."
            ),
            (
                "human",
                "{text}"
            ),
        ]
    )

    map_chain = (
        map_prompt
        | llm
        | StrOutputParser()
    )

    chunk_summaries = []

    for chunk in chunks:

        summary = map_chain.invoke(
            {
                "text": chunk
            }
        )

        if summary:
            chunk_summaries.append(
                summary.strip()
            )

    # ---------------------------------------------------------
    # STEP 3: Partial summaries ko combine karo
    # ---------------------------------------------------------

    combined = "\n\n".join(chunk_summaries)

    if not combined:
        return "Unable to generate summary."

    # ---------------------------------------------------------
    # STEP 4: Final professional summary
    # ---------------------------------------------------------

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. "
                "Combine the provided partial summaries into "
                "one final professional meeting summary.\n\n"
                "Use clear bullet points.\n"
                "Focus on important topics, decisions, "
                "discussion points, and conclusions.\n"
                "Do not add information that is not present "
                "in the provided summaries."
            ),
            (
                "human",
                "{text}"
            ),
        ]
    )

    combined_chain = (
        RunnablePassthrough()
        | RunnableLambda(
            lambda x: {"text": x}
        )
        | combined_prompt
        | llm
        | StrOutputParser()
    )

    return combined_chain.invoke(combined)


def generate_title(transcript: str) -> str:
    """
    Meeting transcript ke basis par short professional title generate karta hai.
    """

    if not transcript:
        return "Untitled Meeting"

    llm = get_llm()

    title_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Based on the meeting transcript, generate a "
                "short professional meeting title. "
                "Maximum 8 words. "
                "Only return the title, nothing else."
            ),
            (
                "human",
                "{text}"
            ),
        ]
    )

    title_chain = (
        title_prompt
        | llm
        | StrOutputParser()
    )

    # Sirf initial 2000 characters title generation ke liye
    title = title_chain.invoke(
        transcript[:2000]
    )

    return title.strip()