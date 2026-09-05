import streamlit as st
import tempfile
import os

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
# CONFIG
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# LOGIN CONFIG
# ============================================================

APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")


# Make sure credentials exist
if not APP_USERNAME or not APP_PASSWORD:
    st.error(
        "⚠️ Login credentials are not configured. "
        "Please add APP_USERNAME and APP_PASSWORD to your .env file."
    )
    st.stop()


# ============================================================
# SESSION STATE - LOGIN
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.session_state.authenticated:

    st.title("🔐 AI Video Assistant")

    st.subheader("Login")

    username = st.text_input(
        "Username",
        placeholder="Enter username",
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter password",
    )

    login_button = st.button(
        "🔑 Login",
        type="primary",
        use_container_width=True,
    )

    if login_button:

        if username == APP_USERNAME and password == APP_PASSWORD:

            st.session_state.authenticated = True

            # Refresh page after successful login
            st.rerun()

        else:

            st.error("❌ Invalid username or password.")

    st.stop()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main title */
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #888888;
        margin-bottom: 30px;
    }

    /* Cards */
    .info-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 15px;
    }

    .card-title {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    /* Chat */
    .user-message {
        background-color: rgba(100,100,255,0.10);
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
    }

    .assistant-message {
        background-color: rgba(100,255,150,0.10);
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "processed" not in st.session_state:
    st.session_state.processed = False

if "result" not in st.session_state:
    st.session_state.result = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Settings")

    # Logout button
    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):
        st.session_state.authenticated = False
        st.session_state.processed = False
        st.session_state.result = None
        st.session_state.chat_history = []

        st.rerun()

    st.divider()

    language = st.selectbox(
        "Transcription Language",
        ["en", "hi"],
        index=0,
    )

    st.divider()

    st.subheader("📌 Supported Input")

    st.write(
        """
        You can provide:

        - 🎥 YouTube URL
        - 🎵 Audio file
        - 🎬 Video file
        """
    )

    st.divider()

    st.caption("AI Video Assistant")
    st.caption("RAG-powered video understanding")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🎥 AI Video Assistant</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Turn long videos into summaries, decisions, action items "
    "and an interactive AI conversation."
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# INPUT SECTION
# ============================================================

st.subheader("📥 Add Your Video")

input_method = st.radio(
    "Choose input method",
    ["YouTube URL", "Upload File"],
    horizontal=True,
)


source = None
uploaded_file = None


if input_method == "YouTube URL":

    source = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
    )

else:

    uploaded_file = st.file_uploader(
        "Upload audio/video",
        type=[
            "mp3",
            "wav",
            "m4a",
            "mp4",
            "mov",
            "avi",
            "mkv",
            "webm",
        ],
    )


# ============================================================
# PROCESS BUTTON
# ============================================================

process_button = st.button(
    "🚀 Analyze Video",
    type="primary",
    use_container_width=True,
)


if process_button:

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if input_method == "YouTube URL":

        if not source:
            st.error("Please enter a YouTube URL.")
            st.stop()

    else:

        if uploaded_file is None:
            st.error("Please upload an audio or video file.")
            st.stop()

    # --------------------------------------------------------
    # Process uploaded file
    # --------------------------------------------------------

    temp_file_path = None

    try:

        if input_method == "Upload File":

            file_extension = os.path.splitext(
                uploaded_file.name
            )[1]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_extension,
            ) as temp_file:

                temp_file.write(
                    uploaded_file.getbuffer()
                )

                temp_file_path = temp_file.name

            source = temp_file_path

        # ----------------------------------------------------
        # Pipeline
        # ----------------------------------------------------

        with st.status(
            "Processing your video...",
            expanded=True,
        ) as status:

            # Step 1
            st.write("🎵 Processing audio/video...")

            chunks = process_input(source)

            st.write(
                f"✅ Audio processed into {len(chunks)} chunk(s)"
            )

            # Step 2
            st.write("🎙️ Transcribing...")

            transcript = transcribe_all(
                chunks,
                language,
            )

            st.write("✅ Transcription completed")

            # Step 3
            st.write("🧠 Generating title...")

            title = generate_title(transcript)

            # Step 4
            st.write("📝 Generating summary...")

            summary = summarize(transcript)

            # Step 5
            st.write("✅ Extracting action items...")

            action_items = extract_action_items(
                transcript
            )

            # Step 6
            st.write("🔑 Extracting key decisions...")

            decisions = extract_key_decisions(
                transcript
            )

            # Step 7
            st.write("❓ Extracting open questions...")

            questions = extract_questions(
                transcript
            )

            # Step 8
            st.write("🔎 Building RAG knowledge base...")

            rag_chain = build_rag_chain(
                transcript
            )

            st.write("✅ RAG system ready")

            status.update(
                label="✅ Video analysis completed!",
                state="complete",
            )

        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        st.session_state.result = {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }

        st.session_state.processed = True

        # Reset chat
        st.session_state.chat_history = []

        st.success(
            "Your video has been successfully analyzed!"
        )

    except Exception as e:

        st.error(
            f"❌ Something went wrong:\n\n{str(e)}"
        )

    finally:

        # Remove temporary uploaded file
        if temp_file_path and os.path.exists(
            temp_file_path
        ):

            try:
                os.remove(temp_file_path)

            except Exception:
                pass


# ============================================================
# RESULTS
# ============================================================

if st.session_state.processed:

    result = st.session_state.result

    st.divider()

    # ========================================================
    # TITLE
    # ========================================================

    st.header(
        f"📌 {result['title']}"
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    st.subheader("📝 Summary")

    st.markdown(
        f"""
        <div class="info-card">
        {result['summary']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # THREE COLUMNS
    # ========================================================

    col1, col2, col3 = st.columns(3)

    # --------------------------------------------------------
    # Action Items
    # --------------------------------------------------------

    with col1:

        st.subheader("✅ Action Items")

        st.markdown(
            f"""
            <div class="info-card">
            {result['action_items']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # Decisions
    # --------------------------------------------------------

    with col2:

        st.subheader("🔑 Key Decisions")

        st.markdown(
            f"""
            <div class="info-card">
            {result['key_decisions']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # Questions
    # --------------------------------------------------------

    with col3:

        st.subheader("❓ Open Questions")

        st.markdown(
            f"""
            <div class="info-card">
            {result['open_questions']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # TRANSCRIPT
    # ========================================================

    st.divider()

    st.subheader("📜 Full Transcript")

    with st.expander(
        "Click to view complete transcript"
    ):

        st.text_area(
            "Transcript",
            result["transcript"],
            height=500,
            label_visibility="collapsed",
        )

        st.download_button(
            label="⬇️ Download Transcript",
            data=result["transcript"],
            file_name="transcript.txt",
            mime="text/plain",
        )

    # ========================================================
    # RAG CHAT
    # ========================================================

    st.divider()

    st.header("💬 Chat with Your Video")

    st.caption(
        "Ask questions about the content of the video."
    )

    # --------------------------------------------------------
    # Display chat history
    # --------------------------------------------------------

    for message in st.session_state.chat_history:

        if message["role"] == "user":

            with st.chat_message("user"):
                st.write(message["content"])

        else:

            with st.chat_message("assistant"):
                st.write(message["content"])

    # --------------------------------------------------------
    # Chat input
    # --------------------------------------------------------

    question = st.chat_input(
        "Ask something about this video..."
    )

    if question:

        # Add user message
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):

            st.write(question)

        # Generate answer
        with st.chat_message("assistant"):

            with st.spinner(
                "Thinking..."
            ):

                try:

                    answer = ask_question(
                        result["rag_chain"],
                        question,
                    )

                    st.write(answer)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                except Exception as e:

                    error_message = (
                        f"Sorry, I couldn't answer that. "
                        f"Error: {str(e)}"
                    )

                    st.error(error_message)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                        }
                    )


# ============================================================
# INITIAL SCREEN
# ============================================================

else:

    st.info(
        "👆 Add a YouTube URL or upload a file, "
        "then click **Analyze Video** to start."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            ### 🎙️ Transcription

            Convert your video's audio into text.
            """
        )

    with col2:

        st.markdown(
            """
            ### 🧠 AI Analysis

            Generate summaries, decisions,
            questions and action items.
            """
        )

    with col3:

        st.markdown(
            """
            ### 💬 RAG Chat

            Ask questions directly about
            your video.
            """
        )