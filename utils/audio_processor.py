import os
import shutil
import tempfile

import yt_dlp
from pydub import AudioSegment

from utils.bgutil_setup import (
    ensure_bgutil_dependencies,
    start_bgutil_server,
    get_bgutil_server_url,
)


# ============================================================
# CONFIG
# ============================================================

# Maximum allowed chunk size
MAX_CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB

# Default chunk length = 10 minutes
DEFAULT_CHUNK_LENGTH_MS = 10 * 60 * 1000

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
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
# FFMPEG
# ============================================================

def check_ffmpeg():

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg not found. "
            "Please install FFmpeg and make sure it is in PATH."
        )

    print(
        f"FFmpeg: {ffmpeg_path}"
    )

    return ffmpeg_path


# ============================================================
# DENO
# ============================================================

def check_deno():

    deno_path = shutil.which("deno")

    if not deno_path:
        raise RuntimeError(
            "Deno not found. "
            "Please install Deno and make sure it is in PATH."
        )

    print(
        f"Deno: {deno_path}"
    )

    return deno_path


# ============================================================
# BGUTIL
# ============================================================

def check_bgutil():

    if not os.path.isdir(BGUTIL_SERVER_DIR):

        raise RuntimeError(
            "BgUtils provider not found:\n"
            f"{BGUTIL_SERVER_DIR}"
        )

    print(
        f"BgUtils provider source found: "
        f"{BGUTIL_SERVER_DIR}"
    )

    return BGUTIL_SERVER_DIR


# ============================================================
# BGUTIL SCRIPT
# ============================================================

def check_bgutil_script():

    if not os.path.isfile(BGUTIL_SCRIPT_PATH):

        raise RuntimeError(
            "BgUtils script not found:\n"
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

def normalize_audio(
    input_path: str,
    output_path: str,
):

    print(
        "\nNormalizing audio..."
    )

    audio = AudioSegment.from_file(
        input_path
    )

    # Mono
    audio = audio.set_channels(
        CHANNELS
    )

    # 16 kHz
    audio = audio.set_frame_rate(
        SAMPLE_RATE
    )

    # 16-bit
    audio = audio.set_sample_width(
        SAMPLE_WIDTH
    )

    # Export WAV
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

    print(
        f"Normalized audio created: "
        f"{output_path}"
    )

    return output_path


# ============================================================
# YOUTUBE OPTIONS
# ============================================================

def build_youtube_options(
    output_dir: str,
    bgutil_server_url: str,
):

    deno_path = check_deno()

    print(
        f"BgUtils URL passed to yt-dlp: "
        f"{bgutil_server_url}"
    )

    extractor_args = {

        "youtube": [
            "player_client=mweb,web_safari,tv,web_embedded"
        ],

        "youtubepot-bgutilhttp": [
            f"base_url={bgutil_server_url}"
        ],

        "youtubepot-bgutilscript": [
            f"server_home={BGUTIL_SERVER_DIR}",
            f"script_path={BGUTIL_SCRIPT_PATH}",
        ],
    }

    options = {

        # Best available audio
        "format": "bestaudio/best",

        # Output file
        "outtmpl": os.path.join(
            output_dir,
            "%(id)s.%(ext)s"
        ),

        # Don't download playlist
        "noplaylist": True,

        # ----------------------------------------------------
        # Deno
        # ----------------------------------------------------

        "js_runtimes": {
            "deno": {
                "paths": [
                    deno_path
                ]
            }
        },

        # ----------------------------------------------------
        # Remote EJS
        # ----------------------------------------------------

        "remote_components": {
            "ejs:npm"
        },

        # ----------------------------------------------------
        # PO Token providers
        # ----------------------------------------------------

        "extractor_args": extractor_args,

        # ----------------------------------------------------
        # Retry
        # ----------------------------------------------------

        "retries": 3,
        "fragment_retries": 3,
        "extractor_retries": 3,

        # ----------------------------------------------------
        # Logs
        # ----------------------------------------------------

        "quiet": False,
        "no_warnings": False,

    }

    return options


# ============================================================
# DOWNLOAD YOUTUBE AUDIO
# ============================================================

def download_youtube_audio(
    url: str,
):

    print(
        "\n"
        + "=" * 60
    )

    print(
        "Starting YouTube audio download"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Check dependencies
    # --------------------------------------------------------

    check_ffmpeg()

    check_deno()

    check_bgutil()

    check_bgutil_script()

    # --------------------------------------------------------
    # BgUtils dependencies
    # --------------------------------------------------------

    print(
        "\nChecking BgUtils dependencies..."
    )

    ensure_bgutil_dependencies()

    print(
        "BgUtils dependencies are ready."
    )

    # --------------------------------------------------------
    # Start BgUtils
    # --------------------------------------------------------

    print(
        "\nStarting/checking BgUtils server..."
    )

    start_bgutil_server()

    bgutil_server_url = (
        get_bgutil_server_url()
    )

    print(
        f"BgUtils server: "
        f"{bgutil_server_url}"
    )

    # --------------------------------------------------------
    # Temporary directory
    # --------------------------------------------------------

    temp_dir = tempfile.mkdtemp(
        prefix="youtube_audio_"
    )

    print(
        f"Temporary directory: "
        f"{temp_dir}"
    )

    # --------------------------------------------------------
    # yt-dlp options
    # --------------------------------------------------------

    ydl_opts = build_youtube_options(
        output_dir=temp_dir,
        bgutil_server_url=bgutil_server_url,
    )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    print(
        "\nDownloading YouTube audio..."
    )

    try:

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

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
            f"\nYouTube download error: "
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

        files = os.listdir(
            temp_dir
        )

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
    # Normalize audio
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
    # Remove original downloaded file
    # --------------------------------------------------------

    if (
        os.path.exists(downloaded_file)
        and downloaded_file != wav_path
    ):

        try:

            os.remove(
                downloaded_file
            )

            print(
                "Original downloaded file removed."
            )

        except Exception as e:

            print(
                f"Could not remove original file: {e}"
            )

    print(
        f"Normalized audio: "
        f"{wav_path}"
    )

    return wav_path


# ============================================================
# LOCAL FILE
# ============================================================

def process_local_file(
    file_path: str,
):

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

    print(
        f"Temporary directory: "
        f"{temp_dir}"
    )

    wav_path = os.path.join(
        temp_dir,
        "normalized_audio.wav"
    )

    normalize_audio(
        file_path,
        wav_path
    )

    print(
        f"Local file processing completed: "
        f"{wav_path}"
    )

    return wav_path


# ============================================================
# SPLIT AUDIO
# ============================================================

def split_audio(
    audio_path: str,
    chunk_length_ms: int = DEFAULT_CHUNK_LENGTH_MS,
):

    print(
        "\n"
        + "=" * 60
    )

    print(
        "Splitting audio"
    )

    print(
        "=" * 60
    )

    print(
        f"Audio file: {audio_path}"
    )

    print(
        f"Chunk length: "
        f"{chunk_length_ms / 60000:.2f} minutes"
    )

    # --------------------------------------------------------
    # Load audio
    # --------------------------------------------------------

    audio = AudioSegment.from_wav(
        audio_path
    )

    duration_ms = len(audio)

    print(
        f"Audio duration: "
        f"{duration_ms / 1000:.2f} seconds"
    )

    print(
        f"Audio duration: "
        f"{duration_ms / 60000:.2f} minutes"
    )

    # --------------------------------------------------------
    # Create chunk directory
    # --------------------------------------------------------

    chunk_dir = tempfile.mkdtemp(
        prefix="audio_chunks_"
    )

    print(
        f"Chunk directory: "
        f"{chunk_dir}"
    )

    chunks = []

    start = 0
    index = 0

    # --------------------------------------------------------
    # Create chunks
    # --------------------------------------------------------

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
        # Check chunk size
        # ----------------------------------------------------

        if file_size > MAX_CHUNK_SIZE:

            print(
                f"\nChunk {index + 1} too large: "
                f"{file_size / (1024 * 1024):.2f} MB"
            )

            print(
                "Reducing chunk length and retrying..."
            )

            shutil.rmtree(
                chunk_dir,
                ignore_errors=True
            )

            return split_audio(
                audio_path,
                max(
                    60 * 1000,
                    chunk_length_ms // 2
                ),
            )

        # ----------------------------------------------------
        # Add chunk
        # ----------------------------------------------------

        chunks.append(
            chunk_path
        )

        print(
            f"Chunk {index + 1}: "
            f"{file_size / (1024 * 1024):.2f} MB"
        )

        start = end
        index += 1

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 60
    )

    print(
        f"Total chunks: {len(chunks)}"
    )

    print(
        "=" * 60
    )

    return chunks


# ============================================================
# MAIN PROCESS INPUT
# ============================================================

def process_input(
    source: str,
    input_type: str = "youtube",
):

    print(
        "\n"
        + "=" * 60
    )

    print(
        "Processing input"
    )

    print(
        "=" * 60
    )

    print(
        f"Input type: {input_type}"
    )

    # --------------------------------------------------------
    # Validate source
    # --------------------------------------------------------

    if not source:

        raise ValueError(
            "Source cannot be empty."
        )

    # --------------------------------------------------------
    # YouTube
    # --------------------------------------------------------

    if input_type == "youtube":

        print(
            "\nSource: YouTube"
        )

        print(
            f"URL: {source}"
        )

        audio_path = (
            download_youtube_audio(
                source
            )
        )

    # --------------------------------------------------------
    # Local file
    # --------------------------------------------------------

    elif input_type == "file":

        print(
            "\nSource: Local file"
        )

        audio_path = (
            process_local_file(
                source
            )
        )

    # --------------------------------------------------------
    # Invalid input type
    # --------------------------------------------------------

    else:

        raise ValueError(
            "Invalid input_type. "
            "Use 'youtube' or 'file'."
        )

    # --------------------------------------------------------
    # Check audio path
    # --------------------------------------------------------

    if not audio_path:

        raise RuntimeError(
            "Audio processing did not return an audio path."
        )

    if not os.path.exists(audio_path):

        raise RuntimeError(
            f"Audio file does not exist: {audio_path}"
        )

    print(
        f"\nAudio ready for splitting:"
    )

    print(
        audio_path
    )

    # --------------------------------------------------------
    # Split audio
    # --------------------------------------------------------

    chunks = split_audio(
        audio_path
    )

    # --------------------------------------------------------
    # Validate chunks
    # --------------------------------------------------------

    if not chunks:

        raise RuntimeError(
            "No audio chunks were generated."
        )

    print(
        "\nAudio processing completed."
    )

    print(
        f"Returning {len(chunks)} chunks to app.py..."
    )

    # IMPORTANT DEBUG MESSAGE
    print(
        "DEBUG: process_input() is returning now."
    )

    return chunks