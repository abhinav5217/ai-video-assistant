import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

BGUTIL_DIR = (
    PROJECT_ROOT /
    "bgutil-ytdlp-pot-provider"
)

BGUTIL_SERVER_DIR = (
    BGUTIL_DIR /
    "server"
)

BGUTIL_MAIN = (
    BGUTIL_SERVER_DIR /
    "src" /
    "main.ts"
)

BGUTIL_SCRIPT = (
    BGUTIL_SERVER_DIR /
    "src" /
    "generate_once.ts"
)


# ============================================================
# SERVER CONFIG
# ============================================================

BGUTIL_HTTP_HOST = "127.0.0.1"

BGUTIL_HTTP_PORT = 4416

BGUTIL_SERVER_URL = (
    f"http://{BGUTIL_HTTP_HOST}:{BGUTIL_HTTP_PORT}"
)


# ============================================================
# VERSION
# ============================================================

BGUTIL_VERSION = "1.3.2"


# ============================================================
# GLOBAL SERVER PROCESS
# ============================================================

_bgutil_process = None


# ============================================================
# FIND DENO
# ============================================================

def get_deno_path():
    """
    Find Deno executable.
    """

    deno = shutil.which("deno")

    if not deno:
        raise RuntimeError(
            "Deno not found. "
            "Please install deno."
        )

    print(
        f"Deno: {deno}"
    )

    return deno


# ============================================================
# ENSURE BGUTIL SOURCE
# ============================================================

def ensure_bgutil_source():
    """
    Make sure BgUtils source exists.

    Normally the repository is already included
    inside the project.
    """

    if (
        BGUTIL_SERVER_DIR.exists()
        and BGUTIL_MAIN.exists()
    ):

        print(
            "BgUtils provider source already exists."
        )

        return BGUTIL_SERVER_DIR

    raise RuntimeError(
        "BgUtils provider source not found.\n"
        f"Expected directory:\n"
        f"{BGUTIL_SERVER_DIR}"
    )


# ============================================================
# ENSURE DEPENDENCIES
# ============================================================

def ensure_bgutil_dependencies():
    """
    Install BgUtils Deno dependencies if required.
    """

    print(
        "Checking BgUtils dependencies..."
    )

    ensure_bgutil_source()

    deno = get_deno_path()

    node_modules = (
        BGUTIL_SERVER_DIR /
        "node_modules"
    )

    # --------------------------------------------------------
    # Already installed
    # --------------------------------------------------------

    if node_modules.exists():

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

    print(
        "Running:"
    )

    print(
        " ".join(command)
    )

    result = subprocess.run(
        command,
        cwd=str(BGUTIL_SERVER_DIR),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:

        print(
            result.stdout
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            "Failed to install BgUtils dependencies."
        )

    print(
        "BgUtils dependencies installed successfully."
    )

    return True


# ============================================================
# CHECK SERVER
# ============================================================

def is_bgutil_server_running():
    """
    Check whether BgUtils HTTP server is responding.
    """

    url = (
        f"{BGUTIL_SERVER_URL}/ping"
    )

    try:

        with urllib.request.urlopen(
            url,
            timeout=2
        ) as response:

            status = response.status

            if status == 200:
                return True

    except Exception:
        return False

    return False


# ============================================================
# START SERVER
# ============================================================

def start_bgutil_server():
    """
    Start BgUtils HTTP server once.
    """

    global _bgutil_process

    # --------------------------------------------------------
    # Already running
    # --------------------------------------------------------

    if is_bgutil_server_running():

        print(
            "BgUtils HTTP server already running."
        )

        return True

    # --------------------------------------------------------
    # Make sure dependencies exist
    # --------------------------------------------------------

    ensure_bgutil_dependencies()

    # --------------------------------------------------------
    # Find Deno
    # --------------------------------------------------------

    deno = get_deno_path()

    if not BGUTIL_MAIN.exists():

        raise RuntimeError(
            f"BgUtils main.ts not found:\n"
            f"{BGUTIL_MAIN}"
        )

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
        "BgUtils command:"
    )

    print(
        " ".join(command)
    )

    # --------------------------------------------------------
    # Start process
    # --------------------------------------------------------

    try:

        _bgutil_process = subprocess.Popen(
            command,
            cwd=str(BGUTIL_SERVER_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    except Exception as e:

        raise RuntimeError(
            f"Could not start BgUtils server: {e}"
        )

    # --------------------------------------------------------
    # Wait for server
    # --------------------------------------------------------

    print(
        "Waiting for BgUtils HTTP server..."
    )

    max_attempts = 30

    for attempt in range(
        max_attempts
    ):

        # ----------------------------------------------------
        # Check process
        # ----------------------------------------------------

        if (
            _bgutil_process.poll()
            is not None
        ):

            output = ""

            try:
                output = (
                    _bgutil_process.stdout.read()
                    if _bgutil_process.stdout
                    else ""
                )
            except Exception:
                pass

            raise RuntimeError(
                "BgUtils HTTP server stopped unexpectedly.\n"
                f"Output:\n{output}"
            )

        # ----------------------------------------------------
        # Check HTTP endpoint
        # ----------------------------------------------------

        if is_bgutil_server_running():

            print(
                f"BgUtils HTTP server ready: "
                f"{BGUTIL_SERVER_URL}"
            )

            return True

        time.sleep(1)

    raise RuntimeError(
        "BgUtils HTTP server did not start "
        f"within {max_attempts} seconds."
    )


# ============================================================
# GET SERVER URL
# ============================================================

def get_bgutil_server_url():
    """
    Return BgUtils HTTP server URL.

    IMPORTANT:
    This function DOES NOT start the server.
    """

    return BGUTIL_SERVER_URL