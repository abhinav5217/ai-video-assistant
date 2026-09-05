import os
import shutil
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BGUTIL_DIR = PROJECT_ROOT / "bgutil-ytdlp-pot-provider"
BGUTIL_SERVER_DIR = BGUTIL_DIR / "server"

BGUTIL_SCRIPT = BGUTIL_SERVER_DIR / "src" / "generate_once.ts"
BGUTIL_MAIN = BGUTIL_SERVER_DIR / "src" / "main.ts"

BGUTIL_VERSION = "1.3.2"

BGUTIL_ZIP_URL = (
    "https://github.com/Brainicism/"
    "bgutil-ytdlp-pot-provider/"
    f"archive/refs/tags/{BGUTIL_VERSION}.zip"
)

BGUTIL_HTTP_HOST = "127.0.0.1"
BGUTIL_HTTP_PORT = 4416

_bgutil_process = None


# ============================================================
# DENO
# ============================================================

def find_deno():
    """
    Find Deno executable.
    """

    deno = shutil.which("deno")

    if deno:
        return deno

    possible_paths = [
        "/opt/homebrew/bin/deno",
        "/usr/local/bin/deno",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


# ============================================================
# DOWNLOAD BGUTIL SOURCE
# ============================================================

def download_bgutil_source():
    """
    Download BgUtils source if it is not available.
    """

    if BGUTIL_SERVER_DIR.exists() and BGUTIL_MAIN.exists():
        print("BgUtils provider source already exists.")
        return True

    print("BgUtils provider source not found.")
    print("Downloading BgUtils provider source...")

    zip_path = PROJECT_ROOT / "bgutil_provider.zip"

    try:
        urllib.request.urlretrieve(
            BGUTIL_ZIP_URL,
            zip_path
        )

        print("BgUtils source downloaded.")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(PROJECT_ROOT)

        extracted_dir = (
            PROJECT_ROOT
            / f"bgutil-ytdlp-pot-provider-{BGUTIL_VERSION}"
        )

        if not extracted_dir.exists():
            raise RuntimeError(
                "Downloaded BgUtils source could not be located."
            )

        if BGUTIL_DIR.exists():
            shutil.rmtree(BGUTIL_DIR)

        extracted_dir.rename(BGUTIL_DIR)

        if not BGUTIL_MAIN.exists():
            raise RuntimeError(
                "BgUtils main.ts was not found after extraction."
            )

        print(
            f"BgUtils provider ready: {BGUTIL_DIR}"
        )

        return True

    except Exception as e:

        print(
            f"BgUtils source download failed: {e}"
        )

        return False

    finally:

        if zip_path.exists():
            try:
                zip_path.unlink()
            except Exception:
                pass


# ============================================================
# INSTALL DEPENDENCIES
# ============================================================

def ensure_bgutil_dependencies():
    """
    Make sure BgUtils source and dependencies are ready.
    """

    if not download_bgutil_source():
        return False

    deno = find_deno()

    if not deno:
        print("Deno not found.")
        return False

    print(f"Deno: {deno}")

    node_modules = BGUTIL_SERVER_DIR / "node_modules"

    # --------------------------------------------------------
    # Check existing dependencies
    # --------------------------------------------------------

    if node_modules.exists():

        try:

            if any(node_modules.iterdir()):

                print(
                    "BgUtils dependencies already installed."
                )

                return True

        except Exception:
            pass

    # --------------------------------------------------------
    # Install dependencies
    # --------------------------------------------------------

    print(
        "Installing BgUtils dependencies..."
    )

    try:

        result = subprocess.run(
            [
                deno,
                "install",
                "--allow-scripts=npm:canvas",
                "--frozen",
            ],
            cwd=str(BGUTIL_SERVER_DIR),
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:

            print(
                "BgUtils dependency installation failed."
            )

            return False

        if not node_modules.exists():

            print(
                "BgUtils node_modules was not created."
            )

            return False

        print(
            "BgUtils dependencies installed successfully."
        )

        return True

    except Exception as e:

        print(
            f"BgUtils dependency installation error: {e}"
        )

        return False


# ============================================================
# START BGUTIL HTTP SERVER
# ============================================================

def start_bgutil_server():
    """
    Start BgUtils HTTP PO Token server.

    Server:
        http://127.0.0.1:4416
    """

    global _bgutil_process

    # --------------------------------------------------------
    # Already running in this Python process
    # --------------------------------------------------------

    if _bgutil_process is not None:

        if _bgutil_process.poll() is None:

            print(
                "BgUtils HTTP server already running."
            )

            return True

        _bgutil_process = None

    # --------------------------------------------------------
    # Make sure dependencies exist
    # --------------------------------------------------------

    if not ensure_bgutil_dependencies():

        raise RuntimeError(
            "Could not setup BgUtils dependencies."
        )

    deno = find_deno()

    if not deno:
        raise RuntimeError(
            "Deno not found."
        )

    if not BGUTIL_MAIN.exists():

        raise RuntimeError(
            f"BgUtils main.ts not found: {BGUTIL_MAIN}"
        )

    # --------------------------------------------------------
    # Check if port already responds
    # --------------------------------------------------------

    ping_url = (
        f"http://{BGUTIL_HTTP_HOST}:"
        f"{BGUTIL_HTTP_PORT}/ping"
    )

    try:

        with urllib.request.urlopen(
            ping_url,
            timeout=2
        ):

            print(
                "BgUtils HTTP server is already running."
            )

            return True

    except Exception:
        pass

    # --------------------------------------------------------
    # Start server
    # --------------------------------------------------------

    print(
        f"Starting BgUtils HTTP server on "
        f"{BGUTIL_HTTP_HOST}:{BGUTIL_HTTP_PORT}..."
    )

    try:

        _bgutil_process = subprocess.Popen(
            [
                deno,
                "run",
                "--allow-all",
                str(BGUTIL_MAIN),
            ],
            cwd=str(BGUTIL_SERVER_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    except Exception as e:

        raise RuntimeError(
            f"Could not start BgUtils HTTP server: {e}"
        )

    # --------------------------------------------------------
    # Wait for server
    # --------------------------------------------------------

    max_wait = 30

    for _ in range(max_wait):

        # Process died
        if _bgutil_process.poll() is not None:

            output = ""

            try:
                output = _bgutil_process.stdout.read()
            except Exception:
                pass

            raise RuntimeError(
                "BgUtils HTTP server stopped unexpectedly.\n"
                f"{output}"
            )

        try:

            with urllib.request.urlopen(
                ping_url,
                timeout=2
            ):

                print(
                    "BgUtils HTTP server is ready."
                )

                return True

        except Exception:

            time.sleep(1)

    raise RuntimeError(
        "BgUtils HTTP server did not become ready "
        f"within {max_wait} seconds."
    )


# ============================================================
# GET SERVER URL
# ============================================================

def get_bgutil_server_url():

    start_bgutil_server()

    return (
        f"http://{BGUTIL_HTTP_HOST}:"
        f"{BGUTIL_HTTP_PORT}"
    )


# ============================================================
# GET SERVER DIRECTORY
# ============================================================

def get_bgutil_server_dir():

    ensure_bgutil_dependencies()

    return str(BGUTIL_SERVER_DIR)