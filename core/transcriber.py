import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_api_key():
    """
    API key ko pehle Streamlit Secrets se,
    phir .env / environment variable se read karega.
    """

    # Streamlit Cloud Secrets
    try:
        import streamlit as st

        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]

    except Exception:
        pass

    # Local .env / environment variable
    api_key = os.getenv("OPENAI_API_KEY")

    return api_key


api_key = get_api_key()

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found. "
        "Add it to Streamlit Secrets or your .env file."
    )


client = OpenAI(api_key=api_key)


def transcribe_chunk(
    chunk_path: str,
    language: str = None,
    translate: bool = False,
    retries: int = 3
) -> str:

    for attempt in range(1, retries + 1):

        try:

            print(
                f"  Sending chunk to OpenAI "
                f"(attempt {attempt}/{retries})..."
            )

            with open(chunk_path, "rb") as audio_file:

                if translate:

                    response = client.audio.translations.create(
                        model="whisper-1",
                        file=audio_file
                    )

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

            print(
                f"  Transcription error: "
                f"{type(e).__name__}: {e}"
            )

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

    full_transcript = []

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