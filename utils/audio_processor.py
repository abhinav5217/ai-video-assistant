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

MAX_CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB
DEFAULT_CHUNK_LENGTH_MS = 10 * 60 * 1000  # 10 minutes

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit


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
# FFmpeg CHECK
# ============================================================

def check_ffmpeg():
    """
    Check whether FFmpeg is installed.
    """

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg not found. Please install FFmpeg."
        )

    print(f"FFmpeg: {ffmpeg_path}")

    return ffmpeg_path


# ============================================================
# DENO CHECK
# ============================================================

def check_deno():
    """
    Check whether Deno is installed.
    """

    deno_path = shutil.which("deno")

    if not deno_path:
        possible_paths = [
            "/opt/homebrew/bin/deno",
            "/usr/local/bin/deno",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                deno_path = path
                break

    if not deno_path:
        raise RuntimeError(
            "Deno not found. Please install Deno."
        )

    print(f"Deno: {deno_path}")

    return deno_path


# ============================================================
# BGUTIL CHECK
# ============================================================

def check_bgutil():
    """
    Check whether BgUtils provider source exists.
    """

    if not os.path.exists(BGUTIL_SERVER_DIR):
        print(
            f"BgUtils provider source not found: "
            f"{BGUTIL_SERVER_DIR}"
        )
        return False

    print(
        f"BgUtils provider source found: "
        f"{BGUTIL_SERVER_DIR}"
    )

    return True


# ============================================================
# BGUTIL SCRIPT CHECK
# ============================================================

def check_bgutil_script():
    """
    Check whether generate_once.ts exists.
    """

    if not os.path.exists(BGUTIL_SCRIPT_PATH):
        print(
            f"BgUtils script not found: "
            f"{BGUTIL_SCRIPT_PATH}"
        )
        return False

    print(
        f"BgUtils script found: "
        f"{BGUTIL_SCRIPT_PATH}"
    )

    return True


# ============================================================
# YOUTUBE OPTIONS
# ============================================================

def build_youtube_options(
    output_dir: str,
    bgutil_server_url: str
):
    """
    Build yt-dlp options for YouTube.

    Uses:
    - Deno for JavaScript challenge solving
    - BgUtils HTTP PO Token server
    - BgUtils script provider
    - Multiple YouTube clients
    """

    deno_path = check_deno()

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

        # ----------------------------------------------------
        # Only one video
        # ----------------------------------------------------

        "noplaylist": True,

        # ----------------------------------------------------
        # Deno JS runtime
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
        # Extractor arguments
        # ----------------------------------------------------

        "extractor_args": {

            "youtube": {
                "player_client": [
                    "mweb",
                    "web_safari",
                    "tv",
                    "web_embedded"
                ]
            },

            # ------------------------------------------------
            # BgUtils script provider
            # ------------------------------------------------

            "youtubepot-bgutilscript": {
                "server_home": BGUTIL_SERVER_DIR,
                "script_path": BGUTIL_SCRIPT_PATH,
            },

            # ------------------------------------------------
            # BgUtils HTTP provider
            # ------------------------------------------------

            "youtubepot-bgutilhttp": {
                "base_url": bgutil_server_url,
            },
        },

        # ----------------------------------------------------
        # Retry
        # ----------------------------------------------------

        "retries": 3,
        "fragment_retries": 3,

        # ----------------------------------------------------
        # Continue download
        # ----------------------------------------------------

        "continuedl": True,
        "overwrites": True,

        # ----------------------------------------------------
        # Timeout
        # ----------------------------------------------------

        "socket_timeout": 30,

        # ----------------------------------------------------
        # Logging
        # ----------------------------------------------------

        "quiet": False,
        "no_warnings": False,

        # ----------------------------------------------------
        # Don't run unnecessary postprocessors
        # ----------------------------------------------------

        "postprocessors": [],
    }

    return options


# ============================================================
# DOWNLOAD YOUTUBE AUDIO
# ============================================================

def download_youtube_audio(url: str):
    """
    Download audio from YouTube.

    Returns:
        Path to normalized WAV file.
    """

    print("\n" + "=" * 60)
    print("Starting YouTube audio download")
    print("=" * 60)

    # --------------------------------------------------------
    # Check FFmpeg
    # --------------------------------------------------------

    check_ffmpeg()

    # --------------------------------------------------------
    # Check Deno
    # --------------------------------------------------------

    check_deno()

    # --------------------------------------------------------
    # Check BgUtils source
    # --------------------------------------------------------

    if not check_bgutil():
        print(
            "BgUtils source missing. "
            "Trying automatic setup..."
        )

    # --------------------------------------------------------
    # Setup BgUtils dependencies
    # --------------------------------------------------------

    print("\nChecking BgUtils dependencies...")

    if not ensure_bgutil_dependencies():
        raise RuntimeError(
            "Could not setup BgUtils PO Token provider."
        )

    print("BgUtils dependencies are ready.")

    # --------------------------------------------------------
    # Check BgUtils script
    # --------------------------------------------------------

    if not check_bgutil_script():
        raise RuntimeError(
            "BgUtils generate_once.ts script was not found."
        )

    # --------------------------------------------------------
    # Start HTTP server
    # --------------------------------------------------------

    print("\nStarting BgUtils HTTP server...")

    if not start_bgutil_server():
        raise RuntimeError(
            "Could not start BgUtils HTTP PO Token server."
        )

    bgutil_server_url = get_bgutil_server_url()

    print(
        f"BgUtils server: {bgutil_server_url}"
    )

    # --------------------------------------------------------
    # Temporary directory
    # --------------------------------------------------------

    temp_dir = tempfile.mkdtemp(
        prefix="youtube_audio_"
    )

    print(
        f"Temporary directory: {temp_dir}"
    )

    # --------------------------------------------------------
    # Build options
    # --------------------------------------------------------

    ydl_opts = build_youtube_options(
        temp_dir,
        bgutil_server_url
    )

    print("\nDownloading YouTube audio...")

    try:

        # ----------------------------------------------------
        # yt-dlp
        # ----------------------------------------------------

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            downloaded_file = ydl.prepare_filename(
                info
            )

        # ----------------------------------------------------
        # Find downloaded audio
        # ----------------------------------------------------

        base_name = os.path.splitext(
            downloaded_file
        )[0]

        possible_extensions = [
            ".webm",
            ".m4a",
            ".mp4",
            ".opus",
            ".mp3",
            ".wav"
        ]

        audio_file = None

        for ext in possible_extensions:

            candidate = base_name + ext

            if os.path.exists(candidate):
                audio_file = candidate
                break

        # ----------------------------------------------------
        # Fallback search
        # ----------------------------------------------------

        if not audio_file:

            for filename in os.listdir(temp_dir):

                if filename.lower().endswith(
                    tuple(possible_extensions)
                ):

                    audio_file = os.path.join(
                        temp_dir,
                        filename
                    )

                    break

        # ----------------------------------------------------
        # File not found
        # ----------------------------------------------------

        if not audio_file:
            raise RuntimeError(
                "YouTube audio file was not found "
                "after download."
            )

        print(
            f"Downloaded audio: {audio_file}"
        )

        # ----------------------------------------------------
        # Normalize
        # ----------------------------------------------------

        wav_path = normalize_audio(
            audio_file,
            temp_dir
        )

        return wav_path

    except Exception as e:

        print(
            f"\nYouTube download error: "
            f"{type(e).__name__}: {e}"
        )

        raise


# ============================================================
# NORMALIZE AUDIO
# ============================================================

def normalize_audio(
    input_path: str,
    output_dir: str
):
    """
    Convert audio to:
    - WAV
    - Mono
    - 16 kHz
    - 16-bit PCM
    """

    print("\nNormalizing audio...")

    try:

        audio = AudioSegment.from_file(
            input_path
        )

        # ----------------------------------------------------
        # Mono
        # ----------------------------------------------------

        audio = audio.set_channels(
            CHANNELS
        )

        # ----------------------------------------------------
        # Sample rate
        # ----------------------------------------------------

        audio = audio.set_frame_rate(
            SAMPLE_RATE
        )

        # ----------------------------------------------------
        # Sample width
        # ----------------------------------------------------

        audio = audio.set_sample_width(
            SAMPLE_WIDTH
        )

        # ----------------------------------------------------
        # Output
        # ----------------------------------------------------

        output_path = os.path.join(
            output_dir,
            "normalized_audio.wav"
        )

        # ----------------------------------------------------
        # Export WAV
        # ----------------------------------------------------

        audio.export(
            output_path,
            format="wav"
        )

        print(
            f"Normalized audio: {output_path}"
        )

        print(
            f"Audio format: "
            f"{audio.channels} channel, "
            f"{audio.frame_rate} Hz, "
            f"{audio.sample_width * 8}-bit"
        )

        return output_path

    except Exception as e:

        raise RuntimeError(
            f"Audio normalization failed: {e}"
        )


# ============================================================
# LOCAL / UPLOADED FILE
# ============================================================

def process_local_file(
    file_path: str
):
    """
    Process uploaded/local audio or video file.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    print(
        f"\nProcessing local file: {file_path}"
    )

    temp_dir = tempfile.mkdtemp(
        prefix="local_audio_"
    )

    wav_path = normalize_audio(
        file_path,
        temp_dir
    )

    return wav_path


# ============================================================
# CREATE TEMP AUDIO
# ============================================================

def create_temp_audio(
    audio: AudioSegment
):
    """
    Save AudioSegment as temporary WAV.
    """

    temp_dir = tempfile.mkdtemp(
        prefix="temp_audio_"
    )

    path = os.path.join(
        temp_dir,
        "audio.wav"
    )

    audio.export(
        path,
        format="wav"
    )

    return path


# ============================================================
# SPLIT AUDIO
# ============================================================

def split_audio(
    audio_path: str,
    chunk_length_ms: int = DEFAULT_CHUNK_LENGTH_MS
):
    """
    Split audio into chunks.

    Target maximum:
        20 MB per chunk

    OpenAI limit:
        25 MB
    """

    print("\nSplitting audio...")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    audio = AudioSegment.from_file(
        audio_path
    )

    duration_ms = len(audio)

    print(
        f"Audio duration: "
        f"{duration_ms / 1000:.2f} seconds"
    )

    chunks_dir = tempfile.mkdtemp(
        prefix="audio_chunks_"
    )

    chunks = []

    chunk_number = 1

    for start in range(
        0,
        duration_ms,
        chunk_length_ms
    ):

        end = min(
            start + chunk_length_ms,
            duration_ms
        )

        chunk = audio[start:end]

        chunk_path = os.path.join(
            chunks_dir,
            f"chunk_{chunk_number:03d}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav"
        )

        file_size = os.path.getsize(
            chunk_path
        )

        # ----------------------------------------------------
        # Too large
        # ----------------------------------------------------

        if file_size > MAX_CHUNK_SIZE:

            print(
                f"Chunk {chunk_number} is too large: "
                f"{file_size / 1024 / 1024:.2f} MB"
            )

            os.remove(chunk_path)

            # ------------------------------------------------
            # Split into smaller chunks
            # ------------------------------------------------

            smaller_audio_path = create_temp_audio(
                chunk
            )

            smaller_chunks = split_audio(
                smaller_audio_path,
                max(
                    chunk_length_ms // 2,
                    60 * 1000
                )
            )

            chunks.extend(
                smaller_chunks
            )

        else:

            chunks.append(
                chunk_path
            )

        chunk_number += 1

    print(
        f"Total chunks: {len(chunks)}"
    )

    return chunks


# ============================================================
# MAIN INPUT PROCESSOR
# ============================================================

def process_input(
    source: str,
    input_type: str = "youtube"
):
    """
    Main processing function.

    input_type:
        youtube
        file
    """

    print("\n" + "=" * 60)
    print("Processing input")
    print("=" * 60)

    print(
        f"Input type: {input_type}"
    )

    # --------------------------------------------------------
    # YouTube
    # --------------------------------------------------------

    if input_type == "youtube":

        audio_path = download_youtube_audio(
            source
        )

    # --------------------------------------------------------
    # Uploaded/local file
    # --------------------------------------------------------

    elif input_type == "file":

        audio_path = process_local_file(
            source
        )

    # --------------------------------------------------------
    # Invalid
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

    print(
        f"Total chunks created: {len(chunks)}"
    )

    return chunks