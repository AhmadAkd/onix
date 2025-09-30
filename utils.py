import os
import sys
import requests
import zipfile
import io
import platform
import tarfile
import subprocess
from packaging import version

from constants import (
    GITHUB_SINGBOX_RELEASE_API,
    GITHUB_XRAY_RELEASE_API,
    SINGBOX_ASSET_KEYWORDS,
    SINGBOX_EXECUTABLE_NAMES,
    XRAY_ASSET_KEYWORDS,
    XRAY_EXECUTABLE_NAMES,
)


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)


def get_singbox_platform_arch():
    """Determines the platform and architecture for the sing-box executable."""
    system = sys.platform
    machine = platform.machine()

    platform_name = None
    arch_name = None

    if system.startswith("win"):
        platform_name = "windows"
        if machine == "AMD64":
            arch_name = "amd64"
    elif system.startswith("linux"):
        platform_name = "linux"
        if machine in ["x86_64", "AMD64"]:
            arch_name = "amd64"
        elif machine in ["aarch64", "arm64"]:
            arch_name = "arm64"
    elif system.startswith("darwin"):  # macOS
        platform_name = "darwin"
        if machine == "x86_64":
            arch_name = "amd64"
        elif machine == "arm64":
            arch_name = "arm64"

    return platform_name, arch_name


def get_local_core_version(core_path, core_name):
    """Gets the version of the local sing-box executable."""
    if not os.path.exists(core_path):
        return None
    try:
        result = subprocess.run(
            [core_path, "version"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        # sing-box: "sing-box version 1.9.0-alpha.4"
        # xray: "Xray 1.8.10 (Xray, Penetrates Everything.) ..."
        version_line = result.stdout.strip()

        # Clean up the version line - remove extra text
        if "Environment:" in version_line:
            version_line = version_line.split("Environment:")[0].strip()

        parts = version_line.split(" ")
        if core_name == "sing-box":
            # Extract version from "sing-box version 1.9.0-alpha.4"
            for part in parts:
                if part.count('.') >= 2:  # Version format like 1.9.0-alpha.4
                    return part
            return parts[2] if len(parts) > 2 else "unknown"
        elif core_name == "xray":
            return parts[1]
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError) as e:
        print(f"ERROR: Could not determine {core_name} version: {e}")
        return None


def get_latest_core_version(api_url):
    """Gets the latest core version from the GitHub API."""
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        release_data = response.json()
        # The tag name is usually the version number, e.g., "v1.9.0"
        latest_version = release_data.get("tag_name", "").lstrip("v")
        return latest_version
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error while fetching latest version: {e}")
        return None


def download_core(asset_url, asset_name, core_path, target_executable_name, callbacks=None):
    """Downloads and extracts the sing-box executable."""
    # Default to print if no callbacks are provided
    callbacks = callbacks or {}
    show_error = callbacks.get(
        'show_error', lambda title, msg: print(f"ERROR [{title}]: {msg}"))

    try:
        print("INFO: Downloading:", asset_name)
        archive_response = requests.get(asset_url, timeout=60)
        archive_response.raise_for_status()

        download_dir = os.path.dirname(core_path)
        if not download_dir:
            download_dir = os.getcwd()

        print(
            "INFO: Extracting", target_executable_name, "from", asset_name + "...")
        if asset_name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(archive_response.content)) as z:
                exe_path_in_archive = next(
                    (
                        name
                        for name in z.namelist()
                        if name.endswith(target_executable_name)
                    ),
                    None,
                )
                if not exe_path_in_archive:
                    raise FileNotFoundError(
                        f"Could not find {target_executable_name} in the zip file."
                    )
                # Extract the file directly to the final destination with the correct name
                with z.open(exe_path_in_archive) as source, open(core_path, "wb") as target:
                    target.write(source.read())
                # Since we extracted directly, no rename is needed.
                # The extracted_path is now just core_path.
                # extracted_path = core_path
                # We don't need the os.rename part anymore for zip files.
                if sys.platform != "win32":
                    os.chmod(core_path, 0o755)
                return True  # Exit early on success

        elif asset_name.endswith(".tar.gz"):
            with tarfile.open(
                fileobj=io.BytesIO(archive_response.content), mode="r:gz"
            ) as tar:
                exe_path_in_archive = next(
                    (
                        member.name
                        for member in tar.getmembers()
                        if member.name.endswith(target_executable_name)
                    ),
                    None,
                )
                if not exe_path_in_archive:
                    raise FileNotFoundError(
                        f"Could not find {target_executable_name} in the tar.gz file."
                    )
                tar.extract(exe_path_in_archive, path=download_dir)
                # extracted_path = os.path.join(
                #     download_dir, exe_path_in_archive)
        else:
            raise ValueError(f"Unsupported archive format: {asset_name}")

        if sys.platform != "win32":
            os.chmod(core_path, 0o755)

        print(
            f"SUCCESS: {target_executable_name} downloaded and extracted successfully!"
        )
        return True

    except requests.exceptions.RequestException as e:
        show_error(
            "Download Error", f"Network error while downloading core: {e}"
        )
        return False
    except (zipfile.BadZipFile, tarfile.ReadError, FileNotFoundError) as e:
        show_error("Extraction Error", f"Failed to extract core: {e}")
        return False
    except Exception as e:
        show_error(
            "Error", f"An unexpected error occurred during download: {e}"
        )
        return False


def download_core_if_needed(core_name="sing-box", force_update=False, callbacks=None):
    """
    Checks for a core executable, compares versions, and downloads if it's missing or outdated.
    """
    callbacks = callbacks or {}
    # Define core-specific details
    core_details = {
        "sing-box": {
            "repo": "SagerNet/sing-box",
            "asset_keywords": SINGBOX_ASSET_KEYWORDS,
            "executable_names": SINGBOX_EXECUTABLE_NAMES,
            "api_url": GITHUB_SINGBOX_RELEASE_API,
        },
        "xray": {
            "repo": "XTLS/Xray-core",
            "asset_keywords": XRAY_ASSET_KEYWORDS,
            "executable_names": XRAY_EXECUTABLE_NAMES,
            "api_url": GITHUB_XRAY_RELEASE_API,
        },
    }

    if core_name not in core_details:
        show_error = callbacks.get(
            'show_error', lambda title, msg: print(f"ERROR [{title}]: {msg}"))
        show_error("Unsupported Core",
                   f"The selected core '{core_name}' is not supported for auto-updates.")
        return

    details = core_details[core_name]
    show_error = callbacks.get(
        'show_error', lambda title, msg: print(f"ERROR [{title}]: {msg}"))

    platform_name, arch_name = get_singbox_platform_arch()
    if not platform_name or not arch_name:
        show_error(
            "Unsupported Platform",
            f"Your OS/Architecture ({sys.platform}/{platform.machine()}) is not supported.",
        )
        return

    target_executable_name = details["executable_names"].get(platform_name)
    core_path = get_resource_path(target_executable_name)

    local_version = get_local_core_version(core_path, core_name)

    if not os.path.exists(core_path):
        print(f"INFO: {core_name} not found. Starting download process.")
        force_update = True  # Force download if it doesn't exist

    if not force_update and local_version:
        latest_version = get_latest_core_version(details["api_url"])
        if not latest_version:
            print(
                f"WARNING: Could not fetch the latest {core_name} version. Skipping update check."
            )
            return

        print(
            f"INFO: Local {core_name} version: {local_version}, Latest version: {latest_version}"
        )

        try:
            if version.parse(local_version) >= version.parse(latest_version):
                print(f"INFO: Your {core_name} core is up to date.")
                return
        except version.InvalidVersion:
            print(
                f"WARNING: Could not parse local version '{local_version}'. Proceeding with update check.")

        # For build script, always proceed with download
        print(f"INFO: Proceeding with {core_name} download/update...")

    print(f"INFO: Proceeding with {core_name} download/update...")
    asset_keyword = details["asset_keywords"].get(
        f"{platform_name}_{arch_name}")

    if not asset_keyword:
        show_error(
            "Asset Error",
            f"No sing-box asset keyword defined for {platform_name}-{arch_name}.",
        )
        return

    try:
        response = requests.get(details["api_url"], timeout=10)
        response.raise_for_status()
        release_data = response.json()

        asset = next(
            (
                asset
                for asset in release_data.get("assets", [])
                if asset_keyword in asset.get("name", "").lower()
            ),
            None,
        )

        if not asset:
            show_error(
                "Asset Error",
                f"Could not find a download link for '{asset_keyword}' in the latest release.",
            )
            return

        if download_core(
            asset["browser_download_url"],
            asset["name"],
            core_path,
            target_executable_name,
            callbacks=callbacks
        ):
            new_version = get_local_core_version(core_path, core_name)
            print(
                "Update Successful:",
                f"{core_name} has been successfully updated to version {new_version}.",
            )

    except requests.exceptions.RequestException as e:
        show_error(
            "API Error", f"Failed to get release information from GitHub: {e}"
        )
