import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BGUTIL_DIR = (
    PROJECT_ROOT / "bgutil-ytdlp-pot-provider"
)

BGUTIL_SERVER_DIR = (
    BGUTIL_DIR / "server"
)

BGUTIL_VERSION = "1.3.2"

BGUTIL_ZIP_URL = (
    "https://github.com/Brainicism/"
    "bgutil-ytdlp-pot-provider/"
    f"archive/refs/tags/{BGUTIL_VERSION}.zip"
)


# ============================================================
# FIND DENO
# ============================================================

def find_deno():
    """
    Find Deno executable.
    """

    deno = shutil.which("deno")

    if deno:
        return deno

    possible_paths = [
        "/usr/local/bin/deno",
        "/opt/homebrew/bin/deno",
        os.path.expanduser("~/.deno/bin/deno"),
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
    Download BgUtils provider source if it is missing.
    """

    src_dir = BGUTIL_SERVER_DIR / "src"

    if src_dir.exists():

        print(
            "BgUtils provider source already exists."
        )

        return True

    print(
        "BgUtils provider source not found."
    )

    print(
        "Downloading BgUtils provider "
        f"version {BGUTIL_VERSION}..."
    )

    zip_path = PROJECT_ROOT / (
        f"bgutil-{BGUTIL_VERSION}.zip"
    )

    try:

        # ----------------------------------------------------
        # Download ZIP
        # ----------------------------------------------------

        urllib.request.urlretrieve(
            BGUTIL_ZIP_URL,
            zip_path,
        )

        print(
            "BgUtils source downloaded."
        )

        # ----------------------------------------------------
        # Extract ZIP
        # ----------------------------------------------------

        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as zip_ref:

            zip_ref.extractall(
                PROJECT_ROOT
            )

        # ----------------------------------------------------
        # GitHub creates:
        #
        # bgutil-ytdlp-pot-provider-1.3.2
        #
        # Rename it to:
        #
        # bgutil-ytdlp-pot-provider
        # ----------------------------------------------------

        extracted_dir = (
            PROJECT_ROOT
            / f"bgutil-ytdlp-pot-provider-{BGUTIL_VERSION}"
        )

        if not extracted_dir.exists():

            raise RuntimeError(
                "Downloaded BgUtils archive was extracted "
                "but expected directory was not found."
            )

        # Remove incomplete directory if present

        if BGUTIL_DIR.exists():

            shutil.rmtree(
                BGUTIL_DIR,
                ignore_errors=True,
            )

        extracted_dir.rename(
            BGUTIL_DIR
        )

        # ----------------------------------------------------
        # Remove ZIP
        # ----------------------------------------------------

        if zip_path.exists():

            zip_path.unlink()

        # ----------------------------------------------------
        # Verify source
        # ----------------------------------------------------

        if not src_dir.exists():

            raise RuntimeError(
                "BgUtils source download completed, "
                "but server/src was not found."
            )

        print(
            "BgUtils provider source ready."
        )

        return True

    except Exception as e:

        print(
            "Failed to download BgUtils provider:"
        )

        print(
            str(e)
        )

        return False


# ============================================================
# INSTALL BGUTIL DEPENDENCIES
# ============================================================

def ensure_bgutil_dependencies():
    """
    Ensure BgUtils source and dependencies exist.
    """

    # --------------------------------------------------------
    # Step 1: Make sure source exists
    # --------------------------------------------------------

    if not download_bgutil_source():

        return False

    # --------------------------------------------------------
    # Step 2: Find Deno
    # --------------------------------------------------------

    deno = find_deno()

    if not deno:

        print(
            "Deno not found."
        )

        return False

    print(
        f"Deno: {deno}"
    )

    # --------------------------------------------------------
    # Step 3: Check node_modules
    # --------------------------------------------------------

    node_modules = (
        BGUTIL_SERVER_DIR / "node_modules"
    )

    if (
        node_modules.exists()
        and any(node_modules.iterdir())
    ):

        print(
            "BgUtils dependencies already installed."
        )

        return True

    # --------------------------------------------------------
    # Step 4: Install dependencies
    # --------------------------------------------------------

    print(
        "Installing BgUtils dependencies..."
    )

    print(
        f"Server directory: "
        f"{BGUTIL_SERVER_DIR}"
    )

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

        # ----------------------------------------------------
        # Verify
        # ----------------------------------------------------

        if (
            node_modules.exists()
            and any(node_modules.iterdir())
        ):

            print(
                "BgUtils dependencies "
                "installed successfully."
            )

            return True

        print(
            "BgUtils installation finished "
            "but node_modules was not found."
        )

        return False

    except subprocess.CalledProcessError as e:

        print(
            "BgUtils dependency installation failed:"
        )

        print(
            str(e)
        )

        return False


# ============================================================
# GET SERVER DIRECTORY
# ============================================================

def get_bgutil_server_dir():

    if not ensure_bgutil_dependencies():

        raise RuntimeError(
            "Could not setup BgUtils PO Token provider."
        )

    return str(
        BGUTIL_SERVER_DIR
    )