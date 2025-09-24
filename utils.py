import os
import sys
import requests
import zipfile
import io
import platform
import tarfile
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


def download_singbox_if_needed():
    """
    Checks for sing-box executable and downloads it from GitHub releases if not found.
    Detects OS and architecture to download the appropriate version.
    Logs progress to the console.
    """
    # 1. Determine OS and Architecture
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

    if not platform_name or not arch_name:
        print(f"ERROR: Unsupported OS/Architecture: {system}/{machine}")
        return

    target_executable_name = SINGBOX_EXECUTABLE_NAMES.get(platform_name)
    if not target_executable_name:
        print(f"ERROR: No executable name defined for platform: {platform_name}")
        return

    singbox_path = get_resource_path(target_executable_name)
    if os.path.exists(singbox_path):
        return

    print(
        f"INFO: {target_executable_name} not found. Attempting to download for {platform_name}-{arch_name} from GitHub..."
    )

    api_url = GITHUB_SINGBOX_RELEASE_API
    asset_keyword = SINGBOX_ASSET_KEYWORDS.get(f"{platform_name}_{arch_name}")

    if not asset_keyword:
        print(
            f"ERROR: No sing-box asset keyword defined for {platform_name}-{arch_name}."
        )
        return

    try:
        # Get latest release information
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        release_data = response.json()

        # Find the correct asset for download
        asset_url = None
        asset_name = None
        for asset in release_data.get("assets", []):
            if asset_keyword in asset.get("name", "").lower():
                asset_url = asset.get("browser_download_url")
                asset_name = asset.get("name")
                break

        if not asset_url:
            print(
                f"ERROR: Could not find a download link for '{asset_keyword}' in the latest release."
            )
            return

        # Download the archive file
        print(f"INFO: Downloading: {asset_name}")
        archive_response = requests.get(asset_url, timeout=60)
        archive_response.raise_for_status()

        download_dir = os.path.dirname(singbox_path)
        if not download_dir:
            download_dir = os.getcwd()

        # Extract the executable
        print(f"INFO: Extracting {target_executable_name} from {asset_name}...")
        if asset_name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(archive_response.content)) as z:
                exe_path_in_archive = None
                for name in z.namelist():
                    if name.endswith(target_executable_name):
                        exe_path_in_archive = name
                        break

                if not exe_path_in_archive:
                    print(
                        f"ERROR: Could not find {target_executable_name} inside the downloaded zip file."
                    )
                    return

                z.extract(exe_path_in_archive, path=download_dir)
                extracted_path = os.path.join(download_dir, exe_path_in_archive)

        elif asset_name.endswith(".tar.gz"):
            with tarfile.open(
                fileobj=io.BytesIO(archive_response.content), mode="r:gz"
            ) as tar:
                exe_path_in_archive = None
                # Find the executable within the tar.gz (often in a subdirectory)
                for member in tar.getmembers():
                    if member.name.endswith(target_executable_name):
                        exe_path_in_archive = member.name
                        break

                if not exe_path_in_archive:
                    print(
                        f"ERROR: Could not find {target_executable_name} inside the downloaded tar.gz file."
                    )
                    return

                tar.extract(exe_path_in_archive, path=download_dir)
                extracted_path = os.path.join(download_dir, exe_path_in_archive)
        else:
            print(f"ERROR: Unsupported archive format: {asset_name}")
            return

        # Move to final location and set permissions
        if extracted_path != singbox_path:
            if os.path.exists(singbox_path):
                os.remove(singbox_path)
            os.rename(extracted_path, singbox_path)

        # Set executable permissions for non-Windows systems
        if platform_name != "windows":
            os.chmod(singbox_path, 0o755)  # rwxr-xr-x

        print(
            f"SUCCESS: {target_executable_name} downloaded and extracted successfully!"
        )

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error while downloading sing-box: {e}")
    except (zipfile.BadZipFile, tarfile.ReadError) as e:
        print(f"ERROR: Downloaded file is corrupted or not a valid archive: {e}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during download: {e}")
