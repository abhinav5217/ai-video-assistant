import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BGUTIL_DIR = PROJECT_ROOT / "bgutil-ytdlp-pot-provider"
BGUTIL_SERVER_DIR = BGUTIL_DIR / "server"

BGUTIL_MAIN = BGUTIL_SERVER_DIR / "src" / "main.ts"
BGUTIL_SCRIPT = BGUTIL_SERVER_DIR / "src" / "generate_once.ts"


# ============================================================
# HTTP SERVER
# ============================================================

BGUTIL_HTTP_HOST = "127.0.0.1"
BGUTIL_HTTP_PORT = 4416

BGUTIL_SERVER_URL = (
    f"http://{BGUTIL_HTTP_HOST}:{BGUTIL_HTTP_PORT}"
)


# ============================================================
# GLOBAL PROCESS
# ============================================================

_bgutil_process = None


# ============================================================
# DENO
# ============================================================

def get_deno_path():
    deno = shutil.which("deno")

    if not deno:
        raise RuntimeError(
            "Deno not found."
        )

    print(f"Deno: {deno}")

    return deno


# ============================================================
# BGUTIL SOURCE
# ============================================================

def ensure_bgutil_source():
    if not BGUTIL_SERVER_DIR.is_dir():
        raise RuntimeError(
            "BgUtils provider not found:\n"
            f"{BGUTIL_SERVER_DIR}"
        )

    if not BGUTIL_MAIN.is_file():
        raise RuntimeError(
            "BgUtils main.ts not found:\n"
            f"{BGUTIL_MAIN}"
        )

    if not BGUTIL_SCRIPT.is_file():
        raise RuntimeError(
            "BgUtils generate_once.ts not found:\n"
            f"{BGUTIL_SCRIPT}"
        )

    print(
        f"BgUtils provider source found: "
        f"{BGUTIL_SERVER_DIR}"
    )

    return True


# ============================================================
# DEPENDENCIES
# ============================================================

def ensure_bgutil_dependencies():

    print("\nChecking BgUtils dependencies...")

    ensure_bgutil_source()

    deno = get_deno_path()

    node_modules = BGUTIL_SERVER_DIR / "node_modules"

    if node_modules.is_dir():

        print(
            "BgUtils dependencies already installed."
        )

        return True

    print(
        "Installing BgUtils dependencies..."
    )

    command = [
        deno,
        "install",
        "--allow-scripts=npm:canvas",
        "--frozen",
    ]

    result = subprocess.run(
        command,
        cwd=str(BGUTIL_SERVER_DIR),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:

        print(result.stdout)
        print(result.stderr)

        raise RuntimeError(
            "Failed to install BgUtils dependencies."
        )

    print(
        "BgUtils dependencies installed successfully."
    )

    return True


# ============================================================
# SERVER HEALTH CHECK
# ============================================================

def is_bgutil_server_running():

    try:

        with urllib.request.urlopen(
            f"{BGUTIL_SERVER_URL}/ping",
            timeout=2,
        ) as response:

            return response.status == 200

    except Exception:

        return False


# ============================================================
# START SERVER
# ============================================================

def start_bgutil_server():

    global _bgutil_process

    # --------------------------------------------------------
    # If server already responds, DO NOT START AGAIN
    # --------------------------------------------------------

    if is_bgutil_server_running():

        print(
            f"BgUtils HTTP server already running: "
            f"{BGUTIL_SERVER_URL}"
        )

        return True

    ensure_bgutil_dependencies()

    deno = get_deno_path()

    print(
        "\nStarting BgUtils HTTP server..."
    )

    command = [
        deno,
        "run",
        "--allow-all",
        str(BGUTIL_MAIN),
    ]

    print(
        "BgUtils command:",
        " ".join(command)
    )

    _bgutil_process = subprocess.Popen(
        command,
        cwd=str(BGUTIL_SERVER_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # --------------------------------------------------------
    # Wait for server
    # --------------------------------------------------------

    for _ in range(30):

        if is_bgutil_server_running():

            print(
                f"BgUtils HTTP server ready: "
                f"{BGUTIL_SERVER_URL}"
            )

            return True

        # Check whether process died
        if _bgutil_process.poll() is not None:

            output = ""

            if _bgutil_process.stdout:

                try:
                    output = (
                        _bgutil_process.stdout.read()
                    )
                except Exception:
                    pass

            raise RuntimeError(
                "BgUtils HTTP server stopped.\n"
                f"{output}"
            )

        time.sleep(1)

    raise RuntimeError(
        "BgUtils HTTP server did not start "
        "within 30 seconds."
    )


# ============================================================
# SERVER URL
# ============================================================

def get_bgutil_server_url():

    return BGUTIL_SERVER_URL