#!/usr/bin/env python3
"""
Universal build script for Onix client
Supports Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def get_platform_info():
    """Get platform-specific information"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return "windows", "amd64", ".exe"
    elif system == "darwin":  # macOS
        if machine in ["arm64", "aarch64"]:
            return "darwin", "arm64", ""
        else:
            return "darwin", "amd64", ""
    elif system == "linux":
        if machine in ["arm64", "aarch64"]:
            return "linux", "arm64", ""
        else:
            return "linux", "amd64", ""
    else:
        raise ValueError(f"Unsupported platform: {system}")


def run_command(cmd, shell=False):
    """Run a command and handle errors"""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd, shell=shell, check=True, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def ensure_dependencies():
    """Ensure all dependencies are installed"""
    print("Checking dependencies...")

    # Check Python version
    if sys.version_info < (3, 9):
        print("Error: Python 3.9+ is required")
        return False

    # Check PyInstaller
    try:
        import PyInstaller

        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        if not run_command([sys.executable, "-m", "pip", "install", "pyinstaller"]):
            return False

    # Install all requirements
    print("Installing all requirements...")
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    ):
        return False
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"]
    ):
        return False

    # Check other dependencies
    try:
        import PySide6

        print(f"PySide6 version: {PySide6.__version__}")
    except ImportError:
        print("Installing PySide6...")
        if not run_command([sys.executable, "-m", "pip", "install", "PySide6"]):
            return False

    return True


def download_cores():
    """Download required cores for the platform"""
    print("Downloading cores...")

    # Download sing-box
    if not run_command([sys.executable, "download_singbox.py"]):
        print("Warning: Failed to download sing-box, continuing...")

    # Download xray if needed
    if not run_command(
        [sys.executable, "-c", "import utils; utils.download_core_if_needed('xray')"]
    ):
        print("Warning: Failed to download xray, continuing...")

    return True  # Continue even if cores fail to download


def compile_translations():
    """Compile translation files"""
    print("Compiling translations...")
    if not run_command([sys.executable, "update_translations.py"]):
        print("Warning: Failed to compile translations, continuing...")

    return True  # Continue even if translations fail


def download_geoip():
    """Download GeoIP database"""
    geoip_path = Path("geoip.db")
    if geoip_path.exists():
        print("GeoIP database already exists")
        return True

    print("Downloading GeoIP database...")
    if platform.system().lower() == "windows":
        cmd = "powershell -Command \"Invoke-WebRequest -Uri 'https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db' -OutFile 'geoip.db'\""
    else:
        cmd = "curl -L -o geoip.db https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db"

    return run_command(cmd, shell=True)


def build_executable():
    """Build the executable using PyInstaller"""
    platform_name, arch_name, ext = get_platform_info()
    executable_name = f"onix{ext}"

    print("Building for", platform_name + "-" + arch_name + "...")

    # Create version.txt
    with open("version.txt", "w") as f:
        f.write("dev")

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={executable_name}",
        "--add-data",
        "version.txt:.",
        "--add-data",
        "geoip.db:.",
        "--add-data",
        "translations:translations",
        "--icon=assets/icon.ico",
        "main.py",
    ]

    # Platform-specific adjustments
    if platform_name == "windows":
        if Path("sing-box.exe").exists():
            cmd.extend(["--add-data", "sing-box.exe:."])
        if Path("xray.exe").exists():
            cmd.extend(["--add-data", "xray.exe:."])
    else:
        if Path("sing-box").exists():
            cmd.extend(["--add-data", "sing-box:."])
        if Path("xray").exists():
            cmd.extend(["--add-data", "xray:."])

    if not run_command(cmd):
        return False

    # Clean up
    os.remove("version.txt")

    return True


def create_package():
    """Create distribution package"""
    platform_name, arch_name, ext = get_platform_info()
    executable_name = f"onix{ext}"

    print("Creating distribution package...")

    # Create package directory
    package_dir = Path(f"dist/onix-{platform_name}-{arch_name}")
    package_dir.mkdir(exist_ok=True)

    # Copy executable
    exe_src = Path(f"dist/{executable_name}")
    exe_dst = package_dir / executable_name
    shutil.copy2(exe_src, exe_dst)

    # Copy additional files
    additional_files = ["README.md", "LICENSE", "CHANGELOG.md"]

    for file in additional_files:
        if Path(file).exists():
            shutil.copy2(file, package_dir)

    # Create archive
    archive_name = f"onix-v1.0.0-{platform_name}-{arch_name}.zip"
    shutil.make_archive(f"dist/{archive_name[:-4]}", "zip", "dist", package_dir.name)

    print(f"Package created: dist/{archive_name}")
    return archive_name


def main():
    """Main build function"""
    print("=" * 50)
    print("    Onix Universal Build Script")
    print("=" * 50)

    platform_name, arch_name, ext = get_platform_info()
    print("Building for:", platform_name + "-" + arch_name)
    print()

    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("Error: main.py not found. Please run from the project root.")
        return False

    # Build steps
    steps = [
        ("Checking dependencies", ensure_dependencies),
        ("Downloading cores", download_cores),
        ("Compiling translations", compile_translations),
        ("Downloading GeoIP", download_geoip),
        ("Building executable", build_executable),
        ("Creating package", create_package),
    ]

    for step_name, step_func in steps:
        print(f"\n--- {step_name} ---")
        if not step_func():
            print(f"Error in step: {step_name}")
            return False

    print("\n" + "=" * 50)
    print("    Build completed successfully!")
    print("=" * 50)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
