import os
import subprocess
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BGUTIL_SERVER_DIR = PROJECT_ROOT / "bgutil-ytdlp-pot-provider" / "server"


def find_deno():
    """
    Find Deno executable.
    """
    deno = shutil.which("deno")

    if deno:
        return deno

    common_paths = [
        "/usr/local/bin/deno",
        "/opt/homebrew/bin/deno",
        os.path.expanduser("~/.deno/bin/deno"),
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


def ensure_bgutil_dependencies():
    """
    Make sure BgUtils server dependencies are installed.

    node_modules is intentionally NOT stored in GitHub.
    It is created automatically on the machine running the app.
    """

    if not BGUTIL_SERVER_DIR.exists():
        print("BgUtils server directory not found.")
        return False

    node_modules = BGUTIL_SERVER_DIR / "node_modules"

    # Already installed
    if node_modules.exists() and any(node_modules.iterdir()):
        print("BgUtils dependencies already installed.")
        return True

    deno = find_deno()

    if not deno:
        print("Deno not found.")
        return False

    print("Installing BgUtils dependencies...")
    print(f"Server directory: {BGUTIL_SERVER_DIR}")
    print(f"Deno: {deno}")

    command = [
        deno,
        "install",
        "--allow-scripts=npm:canvas",
        "--frozen",
    ]

    try:
        subprocess.run(
            command,
            cwd=str(BGUTIL_SERVER_DIR),
            check=True,
        )

        if node_modules.exists():
            print("BgUtils dependencies installed successfully.")
            return True

        print("BgUtils installation completed but node_modules was not found.")
        return False

    except subprocess.CalledProcessError as e:
        print(f"BgUtils installation failed: {e}")
        return False


def get_bgutil_server_dir():
    """
    Return BgUtils server directory.
    """
    ensure_bgutil_dependencies()
    return str(BGUTIL_SERVER_DIR)