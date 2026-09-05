import os
import shutil
import subprocess
import tempfile

import yt_dlp
from pydub import AudioSegment


# ============================================================
# CONFIG
# ============================================================

DOWNLOAD_DIR = "downloads"

# OpenAI request limit is 25 MiB.
# Keep our own limit lower for safety.
MAX_CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB

# 10 minutes
DEFAULT_CHUNK_LENGTH_MS = 10 * 60 * 1000

# Normalize audio for transcription
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ============================================================
# CHECK COMMAND
# ============================================================

def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


# ============================================================
# CHECK FFMPEG
# ============================================================

def check_ffmpeg():
    ffmpeg_path = shutil.which("ffmpeg")

    if ffmpeg_path:
        print("FFmpeg:", ffmpeg_path)
        return True

    print("FFmpeg not found.")
    return False


# ============================================================
# CHECK DENO
# ============================================================

def check_deno():
    deno_path = shutil.which("deno")

    if not deno_path:
        print("Deno: NOT FOUND")
        return False

    try:
        version = subprocess.check_output(
            ["deno", "--version"],
            text=True,
            stderr=subprocess.STDOUT
        )

        print("Deno path:", deno_path)
        print("Deno version:")
        print(version)

        return True

    except Exception as e:
        print("Deno version check failed:", e)
        return False


# ============================================================
# YOUTUBE URL CHECK
# ============================================================

def is_youtube_url(source: str) -> bool:

    if not source:
        return False

    source = source.lower()

    return (
        "youtube.com/" in source
        or "youtu.be/" in source
        or "youtube-nocookie.com/" in source
    )


# ============================================================
# CREATE YOUTUBE DOWNLOAD OPTIONS
# ============================================================

def get_youtube_options(output_template: str):

    return {

        # ----------------------------------------------------
        # IMPORTANT:
        # Prefer HLS audio from web_safari.
        #
        # This avoids normal GVS HTTPS formats which may
        # require a YouTube PO Token and return HTTP 403.
        # ----------------------------------------------------

        "format": (
            "bestaudio[protocol^=m3u8]/"
            "bestaudio/"
            "best"
        ),

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
        # Deno JavaScript runtime
        # ----------------------------------------------------

        "js_runtimes": {
            "deno": {}
        },

        # ----------------------------------------------------
        # yt-dlp EJS components
        # ----------------------------------------------------

        "remote_components": {
            "ejs:npm"
        },

        # ----------------------------------------------------
        # YouTube client
        #
        # web_safari currently provides HLS formats that can
        # avoid the GVS PO-token requirement.
        # ----------------------------------------------------

        "extractor_args": {
            "youtube": {
                "player_client": ["web_safari"]
            }
        },

        # ----------------------------------------------------
        # Browser-like headers
        # ----------------------------------------------------

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },

        # ----------------------------------------------------
        # Convert downloaded audio to WAV
        # ----------------------------------------------------

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav"
            }
        ],

        "quiet": False,

        "no_warnings": False,
    }


# ============================================================
# DOWNLOAD YOUTUBE AUDIO
# ============================================================

def download_youtube_audio(url: str) -> str:

    print("\n========================================")
    print("YOUTUBE DOWNLOAD")
    print("========================================")

    print("YouTube URL:", url)

    # --------------------------------------------------------
    # FFmpeg
    # --------------------------------------------------------

    if not check_ffmpeg():

        raise RuntimeError(
            "FFmpeg is not installed."
        )

    # --------------------------------------------------------
    # Deno
    # --------------------------------------------------------

    if not check_deno():

        raise RuntimeError(
            "YouTube processing requires Deno."
        )

    # --------------------------------------------------------
    # Temporary directory
    # --------------------------------------------------------

    temp_dir = tempfile.mkdtemp(
        prefix="youtube_",
        dir=DOWNLOAD_DIR
    )

    output_template = os.path.join(
        temp_dir,
        "%(id)s.%(ext)s"
    )

    # --------------------------------------------------------
    # yt-dlp options
    # --------------------------------------------------------

    ydl_opts = get_youtube_options(
        output_template
    )

    print("\nYouTube configuration:")
    print("Player client: web_safari")
    print("Preferred protocol: HLS / m3u8")
    print("JavaScript runtime: Deno")

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            print("\nExtracting YouTube information...")

            info = ydl.extract_info(
                url,
                download=True
            )

            print("\nYouTube information extracted.")

            # ------------------------------------------------
            # Original downloaded filename
            # ------------------------------------------------

            original_file = ydl.prepare_filename(
                info
            )

            print(
                "Prepared filename:",
                original_file
            )

            # ------------------------------------------------
            # Expected WAV
            # ------------------------------------------------

            expected_wav = (
                os.path.splitext(original_file)[0]
                + ".wav"
            )

            if os.path.exists(expected_wav):

                print(
                    "\nDownloaded WAV:",
                    expected_wav
                )

                return expected_wav

            # ------------------------------------------------
            # Search temporary directory
            # ------------------------------------------------

            print(
                "\nSearching downloaded files..."
            )

            for filename in os.listdir(temp_dir):

                file_path = os.path.join(
                    temp_dir,
                    filename
                )

                if filename.lower().endswith(".wav"):

                    print(
                        "Downloaded WAV:",
                        file_path
                    )

                    return file_path

            # ------------------------------------------------
            # If WAV wasn't created, look for any media file
            # ------------------------------------------------

            print(
                "WAV not found. Checking downloaded files..."
            )

            for filename in os.listdir(temp_dir):

                file_path = os.path.join(
                    temp_dir,
                    filename
                )

                if os.path.isfile(file_path):

                    print(
                        "Downloaded file:",
                        file_path
                    )

            raise FileNotFoundError(
                "YouTube audio downloaded, "
                "but WAV conversion failed."
            )

    except Exception as e:

        print("\n========================================")
        print("YOUTUBE ERROR")
        print("========================================")

        print(
            "Error type:",
            type(e).__name__
        )

        print(
            "Error:",
            str(e)
        )

        print("========================================")

        # ----------------------------------------------------
        # Helpful 403 message
        # ----------------------------------------------------

        if "403" in str(e):

            print(
                "\nYouTube returned HTTP 403."
            )

            print(
                "The selected YouTube client/format "
                "may require a PO Token."
            )

            print(
                "The application is using web_safari + HLS "
                "as the first workaround."
            )

        raise


# ============================================================
# NORMALIZE AUDIO
# ============================================================

def normalize_audio(
    audio: AudioSegment
) -> AudioSegment:

    """
    Convert audio to:
    - Mono
    - 16 kHz
    - 16-bit PCM

    This dramatically reduces WAV file size.
    """

    print("\nNormalizing audio...")

    audio = audio.set_channels(
        CHANNELS
    )

    audio = audio.set_frame_rate(
        SAMPLE_RATE
    )

    audio = audio.set_sample_width(
        SAMPLE_WIDTH
    )

    print(
        "Audio format:",
        f"{CHANNELS} channel,",
        f"{SAMPLE_RATE} Hz,",
        "16-bit"
    )

    return audio


# ============================================================
# CONVERT TO WAV
# ============================================================

def convert_to_wav(input_path: str) -> str:

    print("\nConverting file to WAV...")

    if not os.path.exists(input_path):

        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    try:

        audio = AudioSegment.from_file(
            input_path
        )

        # Normalize before creating WAV
        audio = normalize_audio(
            audio
        )

        output_path = (
            os.path.splitext(input_path)[0]
            + "_normalized.wav"
        )

        audio.export(
            output_path,
            format="wav"
        )

        file_size = os.path.getsize(
            output_path
        )

        print(
            "Normalized WAV:",
            output_path
        )

        print(
            "WAV size:",
            f"{file_size / (1024 * 1024):.2f} MB"
        )

        return output_path

    except Exception as e:

        print(
            "Audio conversion failed:",
            e
        )

        raise


# ============================================================
# REMOVE OLD CHUNKS
# ============================================================

def clean_old_chunks():

    if not os.path.exists(
        DOWNLOAD_DIR
    ):
        return

    for filename in os.listdir(
        DOWNLOAD_DIR
    ):

        if (
            filename.startswith("chunk_")
            and filename.endswith(".wav")
        ):

            path = os.path.join(
                DOWNLOAD_DIR,
                filename
            )

            try:

                os.remove(path)

            except Exception:
                pass


# ============================================================
# CHUNK AUDIO
# ============================================================

def chunk_audio(
    audio_path: str,
    chunk_length_ms: int = DEFAULT_CHUNK_LENGTH_MS
) -> list:

    """
    Split normalized audio into chunks.

    Audio is:
    - Mono
    - 16 kHz
    - 16-bit WAV
    """

    print("\n========================================")
    print("SPLITTING AUDIO")
    print("========================================")

    if not os.path.exists(
        audio_path
    ):

        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    # --------------------------------------------------------
    # Read audio
    # --------------------------------------------------------

    try:

        audio = AudioSegment.from_file(
            audio_path
        )

    except Exception as e:

        print(
            "Unable to read audio:",
            e
        )

        raise

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    audio = normalize_audio(
        audio
    )

    total_length = len(audio)

    print(
        "Audio duration:",
        round(total_length / 1000, 2),
        "seconds"
    )

    print(
        "Chunk duration:",
        round(chunk_length_ms / 1000, 2),
        "seconds"
    )

    # --------------------------------------------------------
    # Clean old chunks
    # --------------------------------------------------------

    clean_old_chunks()

    chunks = []

    # --------------------------------------------------------
    # Split
    # --------------------------------------------------------

    for start in range(
        0,
        total_length,
        chunk_length_ms
    ):

        end = min(
            start + chunk_length_ms,
            total_length
        )

        chunk = audio[start:end]

        chunk_number = len(chunks) + 1

        chunk_path = os.path.join(
            DOWNLOAD_DIR,
            f"chunk_{chunk_number}.wav"
        )

        # ----------------------------------------------------
        # Export
        # ----------------------------------------------------

        chunk.export(
            chunk_path,
            format="wav"
        )

        # ----------------------------------------------------
        # Check size
        # ----------------------------------------------------

        file_size = os.path.getsize(
            chunk_path
        )

        file_size_mb = (
            file_size / (1024 * 1024)
        )

        # ----------------------------------------------------
        # Safety check
        # ----------------------------------------------------

        if file_size > MAX_CHUNK_SIZE:

            print(
                f"WARNING: Chunk {chunk_number} "
                f"is {file_size_mb:.2f} MB."
            )

            print(
                "Chunk is larger than safety limit."
            )

            os.remove(
                chunk_path
            )

            # Create smaller chunks recursively
            smaller_chunks = chunk_audio_segment(
                audio,
                start,
                end
            )

            chunks.extend(
                smaller_chunks
            )

            continue

        chunks.append(
            chunk_path
        )

        print(
            f"Chunk {chunk_number}: "
            f"{start / 1000:.1f}s - "
            f"{end / 1000:.1f}s "
            f"({file_size_mb:.2f} MB)"
        )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print("\n========================================")
    print("CHUNKING COMPLETED")
    print("========================================")

    print(
        "Total chunks:",
        len(chunks)
    )

    return chunks


# ============================================================
# SAFETY CHUNK FUNCTION
# ============================================================

def chunk_audio_segment(
    audio: AudioSegment,
    start: int,
    end: int
) -> list:

    duration = end - start

    # Prevent infinite recursion
    if duration <= 1000:

        raise RuntimeError(
            "Unable to create a chunk below "
            "the OpenAI upload size limit."
        )

    # Split into half
    middle = start + (
        duration // 2
    )

    segments = [
        (start, middle),
        (middle, end)
    ]

    result = []

    for seg_start, seg_end in segments:

        segment = audio[
            seg_start:seg_end
        ]

        # ----------------------------------------------------
        # Find next chunk number
        # ----------------------------------------------------

        existing_chunks = [
            f
            for f in os.listdir(
                DOWNLOAD_DIR
            )
            if (
                f.startswith("chunk_")
                and f.endswith(".wav")
            )
        ]

        chunk_number = (
            len(existing_chunks) + 1
        )

        chunk_path = os.path.join(
            DOWNLOAD_DIR,
            f"chunk_{chunk_number}.wav"
        )

        # ----------------------------------------------------
        # Export
        # ----------------------------------------------------

        segment.export(
            chunk_path,
            format="wav"
        )

        file_size = os.path.getsize(
            chunk_path
        )

        file_size_mb = (
            file_size / (1024 * 1024)
        )

        # ----------------------------------------------------
        # Still too large
        # ----------------------------------------------------

        if file_size > MAX_CHUNK_SIZE:

            os.remove(
                chunk_path
            )

            result.extend(
                chunk_audio_segment(
                    audio,
                    seg_start,
                    seg_end
                )
            )

        else:

            result.append(
                chunk_path
            )

            print(
                f"Safety chunk: "
                f"{seg_start / 1000:.1f}s - "
                f"{seg_end / 1000:.1f}s "
                f"({file_size_mb:.2f} MB)"
            )

    return result


# ============================================================
# PROCESS INPUT
# ============================================================

def process_input(source: str) -> list:

    print("\n========================================")
    print("PROCESSING INPUT")
    print("========================================")

    if not source:

        raise ValueError(
            "No input source provided."
        )

    # ========================================================
    # YOUTUBE
    # ========================================================

    if is_youtube_url(source):

        print(
            "Input type: YouTube URL"
        )

        audio_path = download_youtube_audio(
            source
        )

    # ========================================================
    # LOCAL / UPLOADED FILE
    # ========================================================

    else:

        print(
            "Input type: Uploaded/local file"
        )

        if not os.path.exists(source):

            raise FileNotFoundError(
                f"File not found: {source}"
            )

        audio_path = source

    # ========================================================
    # CONVERT + NORMALIZE
    # ========================================================

    wav_path = convert_to_wav(
        audio_path
    )

    # ========================================================
    # CHUNK
    # ========================================================

    chunks = chunk_audio(
        wav_path
    )

    # ========================================================
    # COMPLETED
    # ========================================================

    print("\n========================================")
    print("PROCESSING COMPLETED")
    print("========================================")

    return chunks