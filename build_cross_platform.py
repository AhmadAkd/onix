#!/usr/bin/env python3
"""
Cross-platform build script using Docker
Builds for macOS and Linux from Windows
"""

import sys
import subprocess
import platform
from pathlib import Path


def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Docker found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("Docker not found. Please install Docker Desktop.")
    return False


def create_dockerfile(platform_name):
    """Create Dockerfile for specific platform"""
    if platform_name == "linux":
        dockerfile_content = """
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libffi-dev \\
    libssl-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyinstaller

# Copy source code
COPY . .

# Build the application
RUN python build_all.py

# The built files will be in /app/dist
"""
    elif platform_name == "macos":
        # For macOS, we need to use a macOS-based image
        # This is more complex and might not work on Windows
        dockerfile_content = """
FROM --platform=linux/amd64 python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libffi-dev \\
    libssl-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyinstaller

# Copy source code
COPY . .

# Build the application
RUN python build_all.py

# The built files will be in /app/dist
"""

    with open(f"Dockerfile.{platform_name}", "w") as f:
        f.write(dockerfile_content)

    return f"Dockerfile.{platform_name}"


def build_with_docker(platform_name):
    """Build using Docker"""
    print("Building for", platform_name, "using Docker...")

    # Create Dockerfile
    dockerfile = create_dockerfile(platform_name)

    # Build Docker image
    image_name = f"onix-builder-{platform_name}"
    build_cmd = [
        "docker", "build",
        "-f", dockerfile,
        "-t", image_name,
        "."
    ]

    print(f"Building Docker image: {image_name}")
    if not run_command(build_cmd):
        return False

    # Run container and copy files
    container_name = f"onix-build-{platform_name}"
    run_cmd = [
        "docker", "run",
        "--name", container_name,
        image_name,
        "python", "build_all.py"
    ]

    print(f"Running build in container: {container_name}")
    if not run_command(run_cmd):
        return False

    # Copy built files from container
    copy_cmd = [
        "docker", "cp",
        f"{container_name}:/app/dist/",
        f"dist-{platform_name}/"
    ]

    print("Copying built files from container...")
    if not run_command(copy_cmd):
        return False

    # Clean up container
    cleanup_cmd = ["docker", "rm", container_name]
    run_command(cleanup_cmd)

    return True


def run_command(cmd):
    """Run a command and handle errors"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def create_github_workflow():
    """Create a GitHub workflow for cross-platform builds"""
    workflow_content = """
name: Cross-Platform Build

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    - name: Build Windows
      run: python build_all.py
    - name: Upload Windows artifacts
      uses: actions/upload-artifact@v3
      with:
        name: onix-windows
        path: dist/onix-v1.0.0-windows-*.zip

  build-macos:
    runs-on: macos-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    - name: Build macOS
      run: python build_all.py
    - name: Upload macOS artifacts
      uses: actions/upload-artifact@v3
      with:
        name: onix-macos
        path: dist/onix-v1.0.0-darwin-*.zip

  build-linux:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    - name: Build Linux
      run: python build_all.py
    - name: Upload Linux artifacts
      uses: actions/upload-artifact@v3
      with:
        name: onix-linux
        path: dist/onix-v1.0.0-linux-*.zip

  create-release:
    needs: [build-windows, build-macos, build-linux]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
    - name: Download all artifacts
      uses: actions/download-artifact@v3
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: |
          onix-windows/onix-v1.0.0-windows-*.zip
          onix-macos/onix-v1.0.0-darwin-*.zip
          onix-linux/onix-v1.0.0-linux-*.zip
        body: |
          ## Onix v1.0.0 - Multi-Platform Release
          
          ### Downloads
          - **Windows**: `onix-v1.0.0-windows-amd64.zip`
          - **macOS**: `onix-v1.0.0-darwin-amd64.zip` / `onix-v1.0.0-darwin-arm64.zip`
          - **Linux**: `onix-v1.0.0-linux-amd64.zip` / `onix-v1.0.0-linux-arm64.zip`
          
          ### Features
          - Complete UI refactoring with modern PySide6 interface
          - Multi-language support (Persian, Russian, Arabic, Chinese)
          - Comprehensive server management system
          - Health checking and ping services
          - QR code generation for server configurations
          - Advanced routing rules management
          - Subscription management with auto-update
          - System tray integration
          - Modern icon set and UI components
          
          ### Installation
          1. Download the appropriate package for your platform
          2. Extract the archive
          3. Run the executable
          
          ### Requirements
          - Windows 10/11 (64-bit)
          - macOS 10.15+ (Intel/Apple Silicon)
          - Linux (64-bit)
        draft: false
        prerelease: false
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""

    # Create .github/workflows directory if it doesn't exist
    workflows_dir = Path(".github/workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)

    with open(workflows_dir / "cross-platform-build.yml", "w") as f:
        f.write(workflow_content)

    print("GitHub workflow created: .github/workflows/cross-platform-build.yml")


def main():
    """Main function"""
    print("=" * 60)
    print("    Onix Cross-Platform Build Script")
    print("=" * 60)

    # Check if we're on Windows
    if platform.system().lower() != "windows":
        print("This script is designed to run on Windows for cross-platform builds.")
        print("For native builds, use build_all.py directly.")
        return False

    # Check Docker availability
    if not check_docker():
        print("\nDocker is required for cross-platform builds from Windows.")
        print("Please install Docker Desktop and try again.")
        print("\nAlternatively, you can use GitHub Actions for automated builds.")
        create_github_workflow()
        return False

    # Build for different platforms
    platforms = ["linux"]  # macOS requires more complex setup

    for platform_name in platforms:
        print("\n--- Building for", platform_name, "---")
        if not build_with_docker(platform_name):
            print("Failed to build for", platform_name)
            continue

        print("Successfully built for", platform_name)

    print("\n" + "=" * 60)
    print("    Cross-platform build completed!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
