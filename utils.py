import os
import sys
import requests
import zipfile
import io
from constants import GITHUB_SINGBOX_RELEASE_API, SINGBOX_WINDOWS_ASSET_KEYWORD


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)


def download_singbox_if_needed():
    """
    Checks for sing-box.exe and downloads it from GitHub releases if not found.
    Logs progress to the console.
    """
    singbox_path = get_resource_path("sing-box.exe")
    if os.path.exists(singbox_path):
        return

    print("INFO: sing-box.exe not found. Attempting to download from GitHub...")

    api_url = GITHUB_SINGBOX_RELEASE_API
    asset_name_keyword = SINGBOX_WINDOWS_ASSET_KEYWORD

    try:
        # Get latest release information
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        release_data = response.json()

        # Find the correct asset for download
        asset_url = None
        asset_name = None
        for asset in release_data.get("assets", []):
            if asset_name_keyword in asset.get("name", "").lower():
                asset_url = asset.get("browser_download_url")
                asset_name = asset.get("name")
                break

        if not asset_url:
            print(
                f"ERROR: Could not find a download link for '{asset_name_keyword}' in the latest release."
            )
            return

        # Download the zip file
        print(f"INFO: Downloading: {asset_name}")
        zip_response = requests.get(asset_url, timeout=60)
        zip_response.raise_for_status()

        # Extract sing-box.exe from the zip file
        print("INFO: Extracting sing-box.exe...")
        with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
            exe_path_in_zip = None
            for name in z.namelist():
                if name.endswith("sing-box.exe"):
                    exe_path_in_zip = name
                    break

            if not exe_path_in_zip:
                print(
                    "ERROR: Could not find sing-box.exe inside the downloaded zip file."
                )
                return

            z.extract(exe_path_in_zip, path=os.getcwd())

            extracted_path = os.path.join(os.getcwd(), exe_path_in_zip)

            if extracted_path != singbox_path:
                if os.path.exists(singbox_path):
                    os.remove(singbox_path)
                os.rename(extracted_path, singbox_path)

                dir_to_remove = os.path.dirname(extracted_path)
                if dir_to_remove and os.path.isdir(dir_to_remove):
                    try:
                        os.rmdir(dir_to_remove)
                    except OSError:
                        print(
                            f"WARNING: Could not remove temporary directory: {dir_to_remove}"
                        )

        print("SUCCESS: sing-box.exe downloaded and extracted successfully!")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error while downloading sing-box: {e}")
    except zipfile.BadZipFile:
        print("ERROR: Downloaded file is not a valid zip file.")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during download: {e}")
