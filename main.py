from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# LANGUAGE NORMALIZATION
# ============================================================

def normalize_language(language: str | None) -> str | None:
    """
    Convert user-friendly language names into
    ISO-639-1 language codes expected by OpenAI.

    English  -> en
    Hindi    -> hi
    Hinglish -> None (automatic detection)
    """

    if not language:
        return None

    language = language.strip().lower()

    language_map = {
        "english": "en",
        "en": "en",

        "hindi": "hi",
        "hi": "hi",

        # Hinglish is not an ISO-639-1 language.
        # None means automatic language detection.
        "hinglish": None,
    }

    return language_map.get(language, language)


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline(
    source: str,
    language: str | None = "en"
) -> dict:

    print("Starting AI Video Assistant")

    # --------------------------------------------------------
    # Normalize language
    # --------------------------------------------------------

    language = normalize_language(language)

    if language:
        print(f"Transcription language: {language}")
    else:
        print("Transcription language: Automatic detection")

    # --------------------------------------------------------
    # Step 1 - Process audio/video
    # --------------------------------------------------------

    print("\nProcessing audio/video...")

    chunks = process_input(source)

    print(
        f"Audio ready - {len(chunks)} chunk(s) created."
    )

    # --------------------------------------------------------
    # Step 2 - Transcription
    # --------------------------------------------------------

    print("\nTranscribing...")

    transcript = transcribe_all(
        chunks,
        language
    )

    print(
        f"\nRaw transcription "
        f"(first 300 characters):\n"
        f"{transcript[:300]}"
    )

    # --------------------------------------------------------
    # Step 3 - Generate title
    # --------------------------------------------------------

    print("\nGenerating title...")

    title = generate_title(transcript)

    # --------------------------------------------------------
    # Step 4 - Generate summary
    # --------------------------------------------------------

    print("Generating summary...")

    summary = summarize(transcript)

    # --------------------------------------------------------
    # Step 5 - Extract action items
    # --------------------------------------------------------

    print("Extracting action items...")

    action_items = extract_action_items(
        transcript
    )

    # --------------------------------------------------------
    # Step 6 - Extract key decisions
    # --------------------------------------------------------

    print("Extracting key decisions...")

    decisions = extract_key_decisions(
        transcript
    )

    # --------------------------------------------------------
    # Step 7 - Extract questions
    # --------------------------------------------------------

    print("Extracting open questions...")

    questions = extract_questions(
        transcript
    )

    # --------------------------------------------------------
    # Step 8 - Build RAG
    # --------------------------------------------------------

    print("Building RAG knowledge base...")

    rag_chain = build_rag_chain(
        transcript
    )

    print("RAG system ready.")

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


# ============================================================
# CLI ENTRY POINT
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("🎥 AI VIDEO ASSISTANT")
    print("=" * 60)

    # --------------------------------------------------------
    # Get source
    # --------------------------------------------------------

    source = input(
        "\nEnter YouTube URL or local file path: "
    ).strip()

    if not source:
        print("❌ Please provide a YouTube URL or file path.")
        exit()

    # --------------------------------------------------------
    # Get language
    # --------------------------------------------------------

    language_input = input(
        "Language (english/hindi/hinglish): "
    ).strip()

    # Default to English
    if not language_input:
        language_input = "english"

    # Convert to API-compatible language
    language = normalize_language(language_input)

    # --------------------------------------------------------
    # Run pipeline
    # --------------------------------------------------------

    try:

        result = run_pipeline(
            source,
            language
        )

    except Exception as e:

        print("\n❌ Something went wrong:")
        print(e)
        exit()

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    print("\n" + "=" * 60)

    print(
        f"📌 Title: {result['title']}"
    )

    print(
        f"\n📋 Summary:\n"
        f"{result['summary']}"
    )

    print(
        f"\n✅ Action Items:\n"
        f"{result['action_items']}"
    )

    print(
        f"\n🔑 Key Decisions:\n"
        f"{result['key_decisions']}"
    )

    print(
        f"\n❓ Open Questions:\n"
        f"{result['open_questions']}"
    )

    print("=" * 60)

    # ========================================================
    # RAG CHAT
    # ========================================================

    print(
        "\n💬 Chat with your video "
        "(type 'exit' to quit)\n"
    )

    rag_chain = result["rag_chain"]

    while True:

        question = input("You: ").strip()

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        if question.lower() in [
            "exit",
            "quit",
            "q"
        ]:

            print("👋 Goodbye!")
            break

        # ----------------------------------------------------
        # Ignore empty questions
        # ----------------------------------------------------

        if not question:
            continue

        # ----------------------------------------------------
        # Ask RAG
        # ----------------------------------------------------

        try:

            answer = ask_question(
                rag_chain,
                question
            )

            print(
                f"\n🤖 Assistant: {answer}\n"
            )

        except Exception as e:

            print(
                f"\n❌ Error while answering: {e}\n"
            )