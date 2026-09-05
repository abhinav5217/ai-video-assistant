import os
import time

from dotenv import load_dotenv
from openai import OpenAI

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


# Get API key
api_key = get_api_key()

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found. "
        "Add it to Streamlit Secrets or your .env file."
    )


# OpenAI client
client = OpenAI(api_key=api_key)


def transcribe_chunk(
    chunk_path: str,
    language: str = None,
    translate: bool = False,
    retries: int = 3
) -> str:
    """
    Ek audio chunk ko OpenAI Whisper se transcribe karta hai.

    Parameters:
        chunk_path: audio file ka path
        language: language code, example 'en' / 'hi'
        translate: True hone par audio ko English me translate karega
        retries: temporary failure ke liye retry count
    """

    for attempt in range(1, retries + 1):

        try:

            print(
                f"  Sending chunk to OpenAI "
                f"(attempt {attempt}/{retries})..."
            )

            with open(chunk_path, "rb") as audio_file:

                # Translation
                if translate:

                    response = client.audio.translations.create(
                        model="whisper-1",
                        file=audio_file
                    )

                # Transcription
                else:

                    if language:

                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language=language
                        )

                    else:

                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )

            return response.text

        except Exception as e:

            error_message = str(e)

            print(
                f"  Transcription error: "
                f"{type(e).__name__}: {error_message}"
            )

            # 413 = file too large
            # Is error ko retry karne ka koi benefit nahi hai.
            if (
                "413" in error_message
                or "Maximum content size limit" in error_message
                or "Request Entity Too Large" in error_message
            ):

                print(
                    "  Audio file is too large. "
                    "Not retrying this chunk."
                )

                raise

            # Retry temporary errors
            if attempt < retries:

                wait_time = attempt * 3

                print(
                    f"  Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                raise


def transcribe_all(
    chunks: list,
    language: str = None,
    translate: bool = False
) -> str:
    """
    Saare audio chunks ko transcribe karta hai
    aur ek complete transcript return karta hai.
    """

    full_transcript = []

    if not chunks:
        return ""

    for i, chunk in enumerate(chunks):

        print(
            f"\nTranscribing chunk "
            f"{i + 1}/{len(chunks)}"
        )

        text = transcribe_chunk(
            chunk_path=chunk,
            language=language,
            translate=translate
        )

        if text:

            full_transcript.append(
                text.strip()
            )

    print("\nTranscription completed")

    return " ".join(full_transcript)