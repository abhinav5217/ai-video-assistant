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

MAX_CHUNK_SIZE = 20 * 1024 * 1024  # 20 MB

DEFAULT_CHUNK_LENGTH_MS = 10 * 60 * 1000

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

        print(
            "Deno version check failed:",
            e
        )

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
# BUILD YOUTUBE OPTIONS
# ============================================================

def build_youtube_options(
    output_template: str,
    player_client: str
):

    return {

        # ----------------------------------------------------
        # IMPORTANT
        #
        # DO NOT FORCE m3u8.
        #
        # yt-dlp will select a format that is actually
        # available for this video/client.
        # ----------------------------------------------------

        "format": (
            "bestaudio/"
            "best"
        ),

        "outtmpl": output_template,

        "noplaylist": True,

        # ----------------------------------------------------
        # Retry
        # ----------------------------------------------------

        "retries": 5,

        "fragment_retries": 5,

        "file_access_retries": 3,

        "extractor_retries": 3,

        "socket_timeout": 30,

        "continuedl": True,

        # ----------------------------------------------------
        # Deno
        # ----------------------------------------------------

        "js_runtimes": {
            "deno": {}
        },

        # ----------------------------------------------------
        # EJS
        # ----------------------------------------------------

        "remote_components": {
            "ejs:npm"
        },

        # ----------------------------------------------------
        # YouTube client
        # ----------------------------------------------------

        "extractor_args": {
            "youtube": {
                "player_client": [
                    player_client
                ]
            }
        },

        # ----------------------------------------------------
        # User agent
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

            "Accept-Language":
                "en-US,en;q=0.9",

        },

        # ----------------------------------------------------
        # Convert audio to WAV
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
# DOWNLOAD WITH ONE CLIENT
# ============================================================

def try_youtube_download(
    url: str,
    output_template: str,
    player_client: str
):

    print("\n----------------------------------------")

    print(
        "Trying YouTube client:",
        player_client
    )

    print("----------------------------------------")

    ydl_opts = build_youtube_options(
        output_template,
        player_client
    )

    try:

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            return info

    except Exception as e:

        print(
            f"Client {player_client} failed:"
        )

        print(
            type(e).__name__,
            str(e)
        )

        return None


# ============================================================
# DOWNLOAD YOUTUBE AUDIO
# ============================================================

def download_youtube_audio(url: str) -> str:

    print("\n========================================")

    print("YOUTUBE DOWNLOAD")

    print("========================================")

    print(
        "YouTube URL:",
        url
    )

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
    # CLIENT STRATEGY
    #
    # Try clients in order.
    # --------------------------------------------------------

    clients = [
        "web_safari",
        "tv",
        "web_embedded"
    ]

    info = None

    for client in clients:

        info = try_youtube_download(
            url=url,
            output_template=output_template,
            player_client=client
        )

        if info:

            print(
                "\nSuccessful YouTube client:",
                client
            )

            break

    # --------------------------------------------------------
    # All clients failed
    # --------------------------------------------------------

    if not info:

        print("\n========================================")

        print(
            "ALL YOUTUBE DOWNLOAD METHODS FAILED"
        )

        print("========================================")

        raise RuntimeError(
            "YouTube could not provide a downloadable "
            "audio/video format. This can happen because "
            "YouTube is enforcing PO Token/SABR restrictions."
        )

    # --------------------------------------------------------
    # Get expected WAV
    # --------------------------------------------------------

    try:

        with yt_dlp.YoutubeDL(
            {
                "outtmpl": output_template
            }
        ) as ydl:

            original_file = ydl.prepare_filename(
                info
            )

    except Exception:

        original_file = None

    # --------------------------------------------------------
    # Expected WAV
    # --------------------------------------------------------

    if original_file:

        expected_wav = (
            os.path.splitext(
                original_file
            )[0]
            + ".wav"
        )

        if os.path.exists(
            expected_wav
        ):

            print(
                "\nDownloaded WAV:",
                expected_wav
            )

            return expected_wav

    # --------------------------------------------------------
    # Search temp directory
    # --------------------------------------------------------

    print(
        "\nSearching downloaded files..."
    )

    for root, dirs, files in os.walk(
        temp_dir
    ):

        for filename in files:

            file_path = os.path.join(
                root,
                filename
            )

            if filename.lower().endswith(
                ".wav"
            ):

                print(
                    "Downloaded WAV:",
                    file_path
                )

                return file_path

    # --------------------------------------------------------
    # Search any audio file
    # --------------------------------------------------------

    print(
        "WAV not found."
    )

    print(
        "Checking downloaded media..."
    )

    media_extensions = (
        ".m4a",
        ".mp3",
        ".webm",
        ".mp4",
        ".opus"
    )

    for root, dirs, files in os.walk(
        temp_dir
    ):

        for filename in files:

            file_path = os.path.join(
                root,
                filename
            )

            if filename.lower().endswith(
                media_extensions
            ):

                print(
                    "Downloaded media:",
                    file_path
                )

                return file_path

    raise FileNotFoundError(
        "YouTube download completed but "
        "no usable audio file was found."
    )


# ============================================================
# NORMALIZE AUDIO
# ============================================================

def normalize_audio(
    audio: AudioSegment
) -> AudioSegment:

    print(
        "\nNormalizing audio..."
    )

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

def convert_to_wav(
    input_path: str
) -> str:

    print(
        "\nConverting file to WAV..."
    )

    if not os.path.exists(
        input_path
    ):

        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    try:

        audio = AudioSegment.from_file(
            input_path
        )

        audio = normalize_audio(
            audio
        )

        output_path = (
            os.path.splitext(
                input_path
            )[0]
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
    chunk_length_ms: int =
        DEFAULT_CHUNK_LENGTH_MS
) -> list:

    print(
        "\n========================================"
    )

    print(
        "SPLITTING AUDIO"
    )

    print(
        "========================================"
    )

    if not os.path.exists(
        audio_path
    ):

        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

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

    audio = normalize_audio(
        audio
    )

    total_length = len(audio)

    print(
        "Audio duration:",
        round(
            total_length / 1000,
            2
        ),
        "seconds"
    )

    print(
        "Chunk duration:",
        round(
            chunk_length_ms / 1000,
            2
        ),
        "seconds"
    )

    clean_old_chunks()

    chunks = []

    for start in range(
        0,
        total_length,
        chunk_length_ms
    ):

        end = min(
            start + chunk_length_ms,
            total_length
        )

        chunk = audio[
            start:end
        ]

        chunk_number = (
            len(chunks) + 1
        )

        chunk_path = os.path.join(
            DOWNLOAD_DIR,
            f"chunk_{chunk_number}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav"
        )

        file_size = os.path.getsize(
            chunk_path
        )

        file_size_mb = (
            file_size /
            (1024 * 1024)
        )

        if file_size > MAX_CHUNK_SIZE:

            print(
                f"WARNING: Chunk {chunk_number} "
                f"is {file_size_mb:.2f} MB."
            )

            os.remove(
                chunk_path
            )

            smaller_chunks = (
                chunk_audio_segment(
                    audio,
                    start,
                    end
                )
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

    print(
        "\n========================================"
    )

    print(
        "CHUNKING COMPLETED"
    )

    print(
        "========================================"
    )

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

    if duration <= 1000:

        raise RuntimeError(
            "Unable to create a chunk below "
            "the OpenAI upload size limit."
        )

    middle = (
        start +
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

        segment.export(
            chunk_path,
            format="wav"
        )

        file_size = os.path.getsize(
            chunk_path
        )

        file_size_mb = (
            file_size /
            (1024 * 1024)
        )

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

def process_input(
    source: str
) -> list:

    print(
        "\n========================================"
    )

    print(
        "PROCESSING INPUT"
    )

    print(
        "========================================"
    )

    if not source:

        raise ValueError(
            "No input source provided."
        )

    # ========================================================
    # YOUTUBE
    # ========================================================

    if is_youtube_url(
        source
    ):

        print(
            "Input type: YouTube URL"
        )

        audio_path = (
            download_youtube_audio(
                source
            )
        )

    # ========================================================
    # LOCAL / UPLOADED FILE
    # ========================================================

    else:

        print(
            "Input type: Uploaded/local file"
        )

        if not os.path.exists(
            source
        ):

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

    print(
        "\n========================================"
    )

    print(
        "PROCESSING COMPLETED"
    )

    print(
        "========================================"
    )

    return chunks