import os
import sys
import requests
import zipfile
import io
import platform
import tarfile
import subprocess
from tkinter import messagebox
from packaging import version

from constants import (
    GITHUB_SINGBOX_RELEASE_API,
    SINGBOX_ASSET_KEYWORDS,
    SINGBOX_EXECUTABLE_NAMES,
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


def get_local_singbox_version(singbox_path):
    """Gets the version of the local sing-box executable."""
    if not os.path.exists(singbox_path):
        return None
    try:
        result = subprocess.run(
            [singbox_path, "version"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        # Output is like: "sing-box version 1.9.0-alpha.4"
        version_line = result.stdout.strip()
        return version_line.split(" ")[2]
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError) as e:
        print(f"ERROR: Could not determine sing-box version: {e}")
        return None


def get_latest_singbox_version():
    """Gets the latest sing-box version from the GitHub API."""
    try:
        response = requests.get(GITHUB_SINGBOX_RELEASE_API, timeout=10)
        response.raise_for_status()
        release_data = response.json()
        # The tag name is usually the version number, e.g., "v1.9.0"
        latest_version = release_data.get("tag_name", "").lstrip("v")
        return latest_version
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error while fetching latest version: {e}")
        return None


def download_singbox(asset_url, asset_name, singbox_path, target_executable_name):
    """Downloads and extracts the sing-box executable."""
    try:
        print(f"INFO: Downloading: {asset_name}")
        archive_response = requests.get(asset_url, timeout=60)
        archive_response.raise_for_status()

        download_dir = os.path.dirname(singbox_path)
        if not download_dir:
            download_dir = os.getcwd()

        print(f"INFO: Extracting {target_executable_name} from {asset_name}...")
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
                z.extract(exe_path_in_archive, path=download_dir)
                extracted_path = os.path.join(download_dir, exe_path_in_archive)

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
                extracted_path = os.path.join(download_dir, exe_path_in_archive)
        else:
            raise ValueError(f"Unsupported archive format: {asset_name}")

        # Move to final location and set permissions
        if os.path.exists(singbox_path):
            os.remove(singbox_path)
        os.rename(extracted_path, singbox_path)

        if sys.platform != "win32":
            os.chmod(singbox_path, 0o755)

        print(
            f"SUCCESS: {target_executable_name} downloaded and extracted successfully!"
        )
        return True

    except requests.exceptions.RequestException as e:
        messagebox.showerror(
            "Download Error", f"Network error while downloading sing-box: {e}"
        )
        return False
    except (zipfile.BadZipFile, tarfile.ReadError, FileNotFoundError) as e:
        messagebox.showerror("Extraction Error", f"Failed to extract sing-box: {e}")
        return False
    except Exception as e:
        messagebox.showerror(
            "Error", f"An unexpected error occurred during download: {e}"
        )
        return False


def download_singbox_if_needed(force_update=False):
    """
    Checks for sing-box executable, compares versions, and downloads if it's missing or outdated.
    """
    platform_name, arch_name = get_singbox_platform_arch()
    if not platform_name or not arch_name:
        messagebox.showerror(
            "Unsupported Platform",
            f"Your OS/Architecture ({sys.platform}/{platform.machine()}) is not supported.",
        )
        return

    target_executable_name = SINGBOX_EXECUTABLE_NAMES.get(platform_name)
    singbox_path = get_resource_path(target_executable_name)

    local_version = get_local_singbox_version(singbox_path)

    if not os.path.exists(singbox_path):
        print("INFO: sing-box not found. Starting download process.")
        force_update = True  # Force download if it doesn't exist

    if not force_update and local_version:
        latest_version = get_latest_singbox_version()
        if not latest_version:
            print(
                "WARNING: Could not fetch the latest sing-box version. Skipping update check."
            )
            return

        print(
            f"INFO: Local sing-box version: {local_version}, Latest version: {latest_version}"
        )

        try:
            if version.parse(local_version) >= version.parse(latest_version):
                print("INFO: Your sing-box is up to date.")
                return
        except version.InvalidVersion:
            print(
                f"WARNING: Could not parse local version '{local_version}'. Proceeding with update check."
            )

        if not messagebox.askyesno(
            "Update Available",
            f"A new version of sing-box is available ({latest_version}). Your current version is {local_version}.\n\nDo you want to download and update it now?",
        ):
            return

    print("INFO: Proceeding with sing-box download/update...")
    api_url = GITHUB_SINGBOX_RELEASE_API
    asset_keyword = SINGBOX_ASSET_KEYWORDS.get(f"{platform_name}_{arch_name}")

    if not asset_keyword:
        messagebox.showerror(
            "Asset Error",
            f"No sing-box asset keyword defined for {platform_name}-{arch_name}.",
        )
        return

    try:
        response = requests.get(api_url, timeout=10)
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
            messagebox.showerror(
                "Asset Error",
                f"Could not find a download link for '{asset_keyword}' in the latest release.",
            )
            return

        if download_singbox(
            asset["browser_download_url"],
            asset["name"],
            singbox_path,
            target_executable_name,
        ):
            new_version = get_local_singbox_version(singbox_path)
            messagebox.showinfo(
                "Update Successful",
                f"sing-box has been successfully updated to version {new_version}.",
            )

    except requests.exceptions.RequestException as e:
        messagebox.showerror(
            "API Error", f"Failed to get release information from GitHub: {e}"
        )
