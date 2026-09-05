import os
import shutil
import subprocess
import tempfile

import yt_dlp
from pydub import AudioSegment

from utils.bgutil_setup import ensure_bgutil_dependencies


# ============================================================
# CONFIG
# ============================================================

MAX_CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB
DEFAULT_CHUNK_LENGTH_MS = 10 * 60 * 1000  # 10 minutes

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM

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


# ============================================================
# CHECK REQUIRED TOOLS
# ============================================================

def check_ffmpeg():
    """
    Check whether FFmpeg is installed.
    """

    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg not found. Please install FFmpeg."
        )

    print(f"FFmpeg: {ffmpeg}")

    return ffmpeg


def check_deno():
    """
    Check whether Deno is installed.
    """

    deno = shutil.which("deno")

    if not deno:

        possible_paths = [
            "/usr/local/bin/deno",
            "/opt/homebrew/bin/deno",
            os.path.expanduser("~/.deno/bin/deno"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                deno = path
                break

    if not deno:
        raise RuntimeError(
            "Deno not found. Please install Deno."
        )

    print(f"Deno: {deno}")

    return deno


def check_bgutil():
    """
    Check whether BgUtils provider source exists.
    """

    src_dir = os.path.join(
        BGUTIL_SERVER_DIR,
        "src"
    )

    if not os.path.isdir(src_dir):

        print(
            "BgUtils provider source not found:"
            f" {BGUTIL_SERVER_DIR}"
        )

        return False

    print(
        "BgUtils provider:"
        f" {BGUTIL_SERVER_DIR}"
    )

    return True


# ============================================================
# YOUTUBE OPTIONS
# ============================================================

def build_youtube_options(output_template):
    """
    Build yt-dlp options for YouTube.

    BgUtils PO Token provider is used through
    the script provider.
    """

    extractor_args = {
        "youtube": {
            "player_client": [
                "mweb",
                "web_safari",
                "tv",
                "web_embedded",
            ]
        },

        "youtubepot-bgutilscript": {
            "server_home": BGUTIL_SERVER_DIR
        },
    }

    return {

        # ----------------------------------------------------
        # Audio format
        # ----------------------------------------------------

        "format": "bestaudio/best",

        # ----------------------------------------------------
        # Output
        # ----------------------------------------------------

        "outtmpl": output_template,

        "noplaylist": True,

        # ----------------------------------------------------
        # Retry settings
        # ----------------------------------------------------

        "retries": 5,

        "fragment_retries": 5,

        "file_access_retries": 3,

        "extractor_retries": 3,

        "socket_timeout": 30,

        "continuedl": True,

        # ----------------------------------------------------
        # JavaScript runtime
        # ----------------------------------------------------

        "js_runtimes": {
            "deno": {}
        },

        "remote_components": {
            "ejs:npm"
        },

        # ----------------------------------------------------
        # YouTube / PO Token configuration
        # ----------------------------------------------------

        "extractor_args": extractor_args,

        # ----------------------------------------------------
        # Browser-like headers
        # ----------------------------------------------------

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 "
                "Safari/537.36"
            ),

            "Accept-Language": "en-US,en;q=0.9",
        },

        # ----------------------------------------------------
        # Convert downloaded audio to WAV
        # ----------------------------------------------------

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],

        # ----------------------------------------------------
        # Logging
        # ----------------------------------------------------

        "quiet": False,

        "no_warnings": False,
    }


# ============================================================
# FIND DOWNLOADED FILE
# ============================================================

def find_downloaded_audio(temp_dir):
    """
    Find downloaded audio/video file.
    """

    supported_extensions = (
        ".wav",
        ".mp3",
        ".m4a",
        ".webm",
        ".mp4",
        ".opus",
    )

    for filename in os.listdir(temp_dir):

        if filename.lower().endswith(
            supported_extensions
        ):

            return os.path.join(
                temp_dir,
                filename
            )

    return None


# ============================================================
# DOWNLOAD YOUTUBE AUDIO
# ============================================================

def download_youtube_audio(url):
    """
    Download YouTube audio using yt-dlp.

    BgUtils dependencies are installed automatically
    if they are missing.
    """

    print("\n" + "=" * 60)
    print("Starting YouTube download")
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

        raise RuntimeError(
            "BgUtils PO Token provider source "
            "was not found."
        )

    # --------------------------------------------------------
    # Install BgUtils dependencies if needed
    # --------------------------------------------------------

    print(
        "\nChecking BgUtils dependencies..."
    )

    if not ensure_bgutil_dependencies():

        raise RuntimeError(
            "Could not install BgUtils dependencies."
        )

    print(
        "BgUtils dependencies are ready."
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

    try:

        output_template = os.path.join(
            temp_dir,
            "%(id)s.%(ext)s"
        )

        # ----------------------------------------------------
        # Build yt-dlp options
        # ----------------------------------------------------

        ydl_opts = build_youtube_options(
            output_template
        )

        print("\nDownloading YouTube audio...")

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            ydl.download([url])

        # ----------------------------------------------------
        # Find output
        # ----------------------------------------------------

        downloaded_file = find_downloaded_audio(
            temp_dir
        )

        if not downloaded_file:

            raise RuntimeError(
                "YouTube audio download completed "
                "but output file was not found."
            )

        print(
            f"\nDownloaded file:"
            f" {downloaded_file}"
        )

        # ----------------------------------------------------
        # Convert / normalize audio
        # ----------------------------------------------------

        audio = AudioSegment.from_file(
            downloaded_file
        )

        print(
            f"Original audio:"
            f" {audio.channels} channels,"
            f" {audio.frame_rate} Hz,"
            f" {audio.sample_width * 8}-bit"
        )

        # ----------------------------------------------------
        # Normalize
        # ----------------------------------------------------

        audio = (
            audio
            .set_channels(CHANNELS)
            .set_frame_rate(SAMPLE_RATE)
            .set_sample_width(SAMPLE_WIDTH)
        )

        normalized_path = os.path.join(
            temp_dir,
            "normalized.wav"
        )

        audio.export(
            normalized_path,
            format="wav"
        )

        print(
            f"Normalized WAV:"
            f" {normalized_path}"
        )

        print(
            f"Audio format:"
            f" {audio.channels} channel,"
            f" {audio.frame_rate} Hz,"
            f" {audio.sample_width * 8}-bit"
        )

        return normalized_path

    except Exception:

        # Cleanup if download fails

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        raise


# ============================================================
# PROCESS LOCAL FILE
# ============================================================

def process_local_file(file_path):
    """
    Process a locally uploaded audio/video file.
    """

    print("\n" + "=" * 60)
    print("Processing local file")
    print("=" * 60)

    check_ffmpeg()

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    print(
        f"Input file: {file_path}"
    )

    # --------------------------------------------------------
    # Load media
    # --------------------------------------------------------

    audio = AudioSegment.from_file(
        file_path
    )

    print(
        f"Original audio:"
        f" {audio.channels} channels,"
        f" {audio.frame_rate} Hz,"
        f" {audio.sample_width * 8}-bit"
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    audio = (
        audio
        .set_channels(CHANNELS)
        .set_frame_rate(SAMPLE_RATE)
        .set_sample_width(SAMPLE_WIDTH)
    )

    # --------------------------------------------------------
    # Create normalized file
    # --------------------------------------------------------

    temp_dir = tempfile.mkdtemp(
        prefix="local_audio_"
    )

    normalized_path = os.path.join(
        temp_dir,
        "normalized.wav"
    )

    audio.export(
        normalized_path,
        format="wav"
    )

    print(
        f"Normalized WAV:"
        f" {normalized_path}"
    )

    return normalized_path


# ============================================================
# SPLIT AUDIO INTO CHUNKS
# ============================================================

def split_audio(
    audio_path,
    chunk_length_ms=DEFAULT_CHUNK_LENGTH_MS
):
    """
    Split audio into chunks.

    Each chunk is checked against the OpenAI
    25 MB upload limit.
    """

    print("\n" + "=" * 60)
    print("Splitting audio")
    print("=" * 60)

    audio = AudioSegment.from_file(
        audio_path
    )

    total_duration = len(audio)

    print(
        f"Total duration:"
        f" {total_duration / 1000 / 60:.2f} minutes"
    )

    temp_dir = os.path.dirname(
        audio_path
    )

    chunks = []

    start = 0
    chunk_number = 1

    while start < total_duration:

        end = min(
            start + chunk_length_ms,
            total_duration
        )

        chunk = audio[
            start:end
        ]

        chunk_path = os.path.join(
            temp_dir,
            f"chunk_{chunk_number}.wav"
        )

        # ----------------------------------------------------
        # Export chunk
        # ----------------------------------------------------

        chunk.export(
            chunk_path,
            format="wav"
        )

        file_size = os.path.getsize(
            chunk_path
        )

        # ----------------------------------------------------
        # Check file size
        # ----------------------------------------------------

        print(
            f"Chunk {chunk_number}: "
            f"{file_size / 1024 / 1024:.2f} MB"
        )

        # ----------------------------------------------------
        # If chunk is too large, reduce duration
        # ----------------------------------------------------

        if file_size > MAX_CHUNK_SIZE:

            print(
                f"Chunk {chunk_number} is too large."
                " Reducing chunk duration..."
            )

            os.remove(
                chunk_path
            )

            reduced_length = int(
                chunk_length_ms * 0.8
            )

            if reduced_length < 60 * 1000:

                raise RuntimeError(
                    "Could not create an audio chunk "
                    "below the OpenAI upload limit."
                )

            # Recursively create smaller chunks
            smaller_chunks = split_audio(
                audio_path,
                chunk_length_ms=reduced_length
            )

            return smaller_chunks

        chunks.append(
            chunk_path
        )

        start = end
        chunk_number += 1

    print(
        f"\nTotal chunks: {len(chunks)}"
    )

    return chunks


# ============================================================
# MAIN INPUT PROCESSOR
# ============================================================

def process_input(
    source,
    input_type="youtube"
):
    """
    Main input processor.

    input_type:
        youtube
        file
    """

    print("\n" + "=" * 60)
    print("Processing input")
    print("=" * 60)

    # --------------------------------------------------------
    # YouTube
    # --------------------------------------------------------

    if input_type == "youtube":

        audio_path = download_youtube_audio(
            source
        )

    # --------------------------------------------------------
    # Local file
    # --------------------------------------------------------

    elif input_type == "file":

        audio_path = process_local_file(
            source
        )

    else:

        raise ValueError(
            "input_type must be either "
            "'youtube' or 'file'."
        )

    # --------------------------------------------------------
    # Split audio
    # --------------------------------------------------------

    chunks = split_audio(
        audio_path
    )

    return chunks