import os
import shutil
import tempfile
import urllib.request

import yt_dlp
from pydub import AudioSegment

from utils.bgutil_setup import (
    ensure_bgutil_dependencies,
    start_bgutil_server,
    get_bgutil_server_url,
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_CHUNK_SIZE = 20 * 1024 * 1024

DEFAULT_CHUNK_LENGTH_MS = 10 * 60 * 1000

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

BGUTIL_DIR = os.path.join(
    PROJECT_ROOT,
    "bgutil-ytdlp-pot-provider"
)

BGUTIL_SERVER_DIR = os.path.join(
    BGUTIL_DIR,
    "server"
)

BGUTIL_SCRIPT_PATH = os.path.join(
    BGUTIL_SERVER_DIR,
    "src",
    "generate_once.ts"
)


# ============================================================
# CHECK FFMPEG
# ============================================================

def check_ffmpeg():
    """
    Check whether FFmpeg is installed.
    """

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg not found. "
            "Please install FFmpeg or add it to packages.txt."
        )

    print(f"FFmpeg: {ffmpeg_path}")

    return ffmpeg_path


# ============================================================
# CHECK DENO
# ============================================================

def check_deno():
    """
    Check whether Deno is installed.
    """

    deno_path = shutil.which("deno")

    if not deno_path:
        raise RuntimeError(
            "Deno not found. "
            "Please make sure deno is installed from requirements.txt."
        )

    print(f"Deno: {deno_path}")

    return deno_path


# ============================================================
# CHECK BGUTIL
# ============================================================

def check_bgutil():
    """
    Check whether BgUtils provider source exists.
    """

    if not os.path.isdir(BGUTIL_SERVER_DIR):
        raise RuntimeError(
            f"BgUtils provider not found:\n{BGUTIL_SERVER_DIR}"
        )

    print(
        f"BgUtils provider source found: "
        f"{BGUTIL_SERVER_DIR}"
    )

    return BGUTIL_SERVER_DIR


# ============================================================
# CHECK BGUTIL SCRIPT
# ============================================================

def check_bgutil_script():
    """
    Check whether generate_once.ts exists.
    """

    if not os.path.isfile(BGUTIL_SCRIPT_PATH):
        raise RuntimeError(
            f"BgUtils script not found:\n"
            f"{BGUTIL_SCRIPT_PATH}"
        )

    print(
        f"BgUtils script found: "
        f"{BGUTIL_SCRIPT_PATH}"
    )

    return BGUTIL_SCRIPT_PATH


# ============================================================
# NORMALIZE AUDIO
# ============================================================

def normalize_audio(input_path: str, output_path: str):
    """
    Convert audio to:
    - WAV
    - Mono
    - 16 kHz
    - 16-bit PCM

    This keeps OpenAI Whisper chunks small enough.
    """

    print("\nNormalizing audio...")

    audio = AudioSegment.from_file(input_path)

    audio = audio.set_channels(CHANNELS)
    audio = audio.set_frame_rate(SAMPLE_RATE)
    audio = audio.set_sample_width(SAMPLE_WIDTH)

    audio.export(
        output_path,
        format="wav"
    )

    print(
        f"Audio format: "
        f"{CHANNELS} channel, "
        f"{SAMPLE_RATE} Hz, "
        f"{SAMPLE_WIDTH * 8}-bit"
    )

    return output_path


# ============================================================
# CREATE TEMP AUDIO
# ============================================================

def create_temp_audio():
    """
    Create temporary directory for downloaded audio.
    """

    temp_dir = tempfile.mkdtemp(
        prefix="youtube_audio_"
    )

    print(f"Temporary directory: {temp_dir}")

    return temp_dir


# ============================================================
# BUILD YOUTUBE OPTIONS
# ============================================================

def build_youtube_options(
    output_dir: str,
    bgutil_server_url: str,
):
    """
    Build yt-dlp configuration.

    IMPORTANT:
    extractor_args values are passed as LISTS.

    This prevents the:
    Unsupported url scheme: ""
    error from bgutil HTTP provider.
    """

    deno_path = check_deno()

    print(
        f"Building yt-dlp options..."
    )

    print(
        f"BgUtils HTTP server URL: "
        f"{bgutil_server_url}"
    )

    options = {

        # ----------------------------------------------------
        # Audio format
        # ----------------------------------------------------

        "format": "bestaudio/best",

        # ----------------------------------------------------
        # Output
        # ----------------------------------------------------

        "outtmpl": os.path.join(
            output_dir,
            "%(id)s.%(ext)s"
        ),

        "noplaylist": True,

        # ----------------------------------------------------
        # Deno JavaScript runtime
        # ----------------------------------------------------

        "js_runtimes": {
            "deno": {
                "paths": [deno_path]
            }
        },

        # ----------------------------------------------------
        # Remote EJS components
        # ----------------------------------------------------

        "remote_components": {
            "ejs:npm"
        },

        # ----------------------------------------------------
        # YouTube / PO Token configuration
        # ----------------------------------------------------

        "extractor_args": {

            # YouTube player clients
            "youtube": [
                "player_client=mweb,web_safari,tv,web_embedded"
            ],

            # ------------------------------------------------
            # BgUtils HTTP provider
            #
            # IMPORTANT:
            # base_url MUST be a list-style extractor arg.
            # ------------------------------------------------

            "youtubepot-bgutilhttp": [
                f"base_url={bgutil_server_url}"
            ],

            # ------------------------------------------------
            # BgUtils script provider fallback
            # ------------------------------------------------

            "youtubepot-bgutilscript": [
                f"server_home={BGUTIL_SERVER_DIR}",
                f"script_path={BGUTIL_SCRIPT_PATH}",
            ],
        },

        # ----------------------------------------------------
        # Retry / network settings
        # ----------------------------------------------------

        "retries": 3,

        "fragment_retries": 3,

        "extractor_retries": 3,

        # ----------------------------------------------------
        # Continue disabled
        # ----------------------------------------------------

        "continuedl": False,

        # ----------------------------------------------------
        # Quiet disabled so logs are visible
        # ----------------------------------------------------

        "quiet": False,

        "no_warnings": False,

        # ----------------------------------------------------
        # Avoid playlist
        # ----------------------------------------------------

        "noplaylist": True,
    }

    return options


# ============================================================
# DOWNLOAD YOUTUBE AUDIO
# ============================================================

def download_youtube_audio(
    url: str,
):
    """
    Download YouTube audio and convert it to normalized WAV.
    """

    print("\nStarting YouTube audio download")

    # --------------------------------------------------------
    # Check dependencies
    # --------------------------------------------------------

    check_ffmpeg()

    check_deno()

    check_bgutil()

    check_bgutil_script()

    # --------------------------------------------------------
    # Ensure BgUtils dependencies
    # --------------------------------------------------------

    print("\nChecking BgUtils dependencies...")

    ensure_bgutil_dependencies()

    print("BgUtils dependencies are ready.")

    # --------------------------------------------------------
    # Start BgUtils HTTP server ONCE
    # --------------------------------------------------------

    start_bgutil_server()

    bgutil_server_url = get_bgutil_server_url()

    print(
        f"BgUtils server: "
        f"{bgutil_server_url}"
    )

    # --------------------------------------------------------
    # Create temporary directory
    # --------------------------------------------------------

    temp_dir = create_temp_audio()

    # --------------------------------------------------------
    # Build yt-dlp options
    # --------------------------------------------------------

    ydl_opts = build_youtube_options(
        output_dir=temp_dir,
        bgutil_server_url=bgutil_server_url,
    )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    print("\nDownloading YouTube audio...")

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            if not info:
                raise RuntimeError(
                    "Could not extract YouTube information."
                )

            downloaded_file = (
                ydl.prepare_filename(info)
            )

    except Exception as e:

        print(
            "\nYouTube download failed:"
        )

        print(
            f"{type(e).__name__}: {e}"
        )

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        raise

    # --------------------------------------------------------
    # Find downloaded file
    # --------------------------------------------------------

    if not os.path.exists(downloaded_file):

        files = os.listdir(temp_dir)

        if not files:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

            raise RuntimeError(
                "YouTube audio file was not downloaded."
            )

        downloaded_file = os.path.join(
            temp_dir,
            files[0]
        )

    print(
        f"Downloaded file: "
        f"{downloaded_file}"
    )

    # --------------------------------------------------------
    # Convert to WAV
    # --------------------------------------------------------

    wav_path = os.path.join(
        temp_dir,
        "normalized_audio.wav"
    )

    normalize_audio(
        downloaded_file,
        wav_path
    )

    # --------------------------------------------------------
    # Delete original downloaded file
    # --------------------------------------------------------

    if (
        os.path.exists(downloaded_file)
        and downloaded_file != wav_path
    ):

        try:
            os.remove(downloaded_file)
        except Exception:
            pass

    print(
        f"Normalized audio: "
        f"{wav_path}"
    )

    return wav_path


# ============================================================
# PROCESS LOCAL FILE
# ============================================================

def process_local_file(
    file_path: str,
):
    """
    Process an uploaded local audio/video file.
    """

    print(
        f"\nProcessing local file: "
        f"{file_path}"
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    temp_dir = tempfile.mkdtemp(
        prefix="local_audio_"
    )

    wav_path = os.path.join(
        temp_dir,
        "normalized_audio.wav"
    )

    normalize_audio(
        file_path,
        wav_path
    )

    return wav_path


# ============================================================
# SPLIT AUDIO
# ============================================================

def split_audio(
    audio_path: str,
    chunk_length_ms: int = DEFAULT_CHUNK_LENGTH_MS,
):
    """
    Split audio into chunks.

    Each chunk is checked against the
    OpenAI 25 MB limit.

    Target maximum:
    20 MB
    """

    print("\nSplitting audio...")

    audio = AudioSegment.from_wav(
        audio_path
    )

    duration_ms = len(audio)

    print(
        f"Audio duration: "
        f"{duration_ms / 1000:.2f} seconds"
    )

    chunks = []

    chunk_dir = tempfile.mkdtemp(
        prefix="audio_chunks_"
    )

    start = 0
    index = 0

    while start < duration_ms:

        end = min(
            start + chunk_length_ms,
            duration_ms
        )

        chunk = audio[
            start:end
        ]

        chunk_path = os.path.join(
            chunk_dir,
            f"chunk_{index:03d}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav"
        )

        file_size = os.path.getsize(
            chunk_path
        )

        # ----------------------------------------------------
        # If chunk is too large, split it recursively
        # ----------------------------------------------------

        if file_size > MAX_CHUNK_SIZE:

            print(
                f"Chunk {index + 1} is too large: "
                f"{file_size / (1024 * 1024):.2f} MB"
            )

            os.remove(chunk_path)

            # Process smaller chunk size
            smaller_chunks = split_audio(
                audio_path=audio_path,
                chunk_length_ms=max(
                    60 * 1000,
                    chunk_length_ms // 2
                ),
            )

            return smaller_chunks

        chunks.append(
            chunk_path
        )

        print(
            f"Chunk {index + 1}: "
            f"{file_size / (1024 * 1024):.2f} MB"
        )

        start = end
        index += 1

    print(
        f"Total chunks: "
        f"{len(chunks)}"
    )

    return chunks


# ============================================================
# MAIN INPUT PROCESSOR
# ============================================================

def process_input(
    source: str,
    input_type: str = "youtube",
):
    """
    Main processing function.

    input_type:
        youtube
        file

    Returns:
        list of audio chunk paths
    """

    print("\nProcessing input")

    print(
        f"Input type: "
        f"{input_type}"
    )

    # --------------------------------------------------------
    # YouTube
    # --------------------------------------------------------

    if input_type == "youtube":

        audio_path = download_youtube_audio(
            source
        )

    # --------------------------------------------------------
    # Uploaded file
    # --------------------------------------------------------

    elif input_type == "file":

        audio_path = process_local_file(
            source
        )

    # --------------------------------------------------------
    # Invalid input
    # --------------------------------------------------------

    else:

        raise ValueError(
            "Invalid input_type. "
            "Use 'youtube' or 'file'."
        )

    # --------------------------------------------------------
    # Split audio
    # --------------------------------------------------------

    chunks = split_audio(
        audio_path
    )

    print(
        "\nAudio processing completed."
    )

    return chunks