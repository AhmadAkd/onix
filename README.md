# Onix - A Modern GUI Client for Sing-box

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/network/members)

---

**Languages:** [English](README.md) | [فارسی](README_fa.md) | [Русский](README_ru.md) | [简体中文](README_zh.md)

---

Onix is a graphical user interface (GUI) client for Sing-box, designed to simplify managing your connections. Built with `customtkinter`, it offers a modern, feature-rich, and user-friendly interface for Windows.

## ✨ Features

- **Extensive Protocol Support:** 
  - **Standard Protocols:** VLESS, VMess, Shadowsocks, Trojan.
  - **Modern Protocols:** **TUIC (v5)**, **Hysteria2**, and **WireGuard**.
- **Automatic Core Management:** Onix automatically downloads and manages the latest `sing-box` core for you.
- **Advanced Subscription Management:**
    - Add, edit, and delete multiple subscription links.
    - Enable or disable individual subscriptions.
    - Update all subscriptions with a single click to fetch the latest servers.
- **Powerful Server Management:**
    - Add servers from subscription links.
    - Add servers manually via share links.
    - Add servers by scanning QR codes directly from your screen.
    - **Import WireGuard configs** directly from `.conf` files.
    - Organize servers into groups for better management.
- **Enhanced UI & UX:**
    - **Search Bar:** Instantly filter your server list by name.
    - **Sortable Columns:** Sort servers by name or ping latency with a single click.
    - **Interactive Log Panel:** Filter logs by level (Info, Warning, Error, etc.) to easily debug issues.
    - **Visual Feedback:** See "..." indicators next to servers during latency tests.
- **Connection Testing & Analysis:**
    - Perform TCP pings and URL tests for your servers to check their performance.
    - Sort servers by ping results to easily find the fastest one.
- **System Integration (Windows):**
    - Easily enable or disable the system-wide proxy.
    - Run the application in the system tray for discreet operation.
    - **TUN Mode:** Enable system-wide proxying for all applications.
- **Advanced Configuration:**
    - **Connection Mode:** Switch between Rule-Based and Global proxy modes.
    - **Configurable Muxing:** Enable and configure multiplexing (h2mux, smux, yamux) to improve performance.
    - **Hysteria2 Bandwidth:** Set default upload and download speeds for Hysteria2 connections.
    - **Custom DNS:** Set custom DNS servers.
    - **Bypass Rules:** Configure domains and IPs to bypass the proxy.
    - **Custom Routing:** Define advanced, custom rules to control how network traffic is routed (e.g., by domain, IP, process, geosite, or geoip).
- **Profile Management:**
    - **Import/Export:** Easily import and export your entire application profile (including servers, subscriptions, and settings) as a single JSON file.

## 🚀 Getting Started

### Download and Run (For Users)

You don't need Python installed to use Onix. Simply download the latest executable (EXE) from the [Releases](https://github.com/AhmadAkd/onix/releases) section on GitHub.

1. Go to the [Releases page](https://github.com/AhmadAkd/onix/releases).
2. Find the latest release and download the `onix-windows-exe.zip` file.
3. Extract the ZIP file.
4. Run the `onix.exe` file.

**Note:** The `sing-box.exe` file is automatically downloaded and managed by Onix, so you do not need to download it separately.

### For Developers

#### Prerequisites

- Python 3.8+
- `pip` (Python package installer)

#### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/AhmadAkd/onix.git
    cd onix
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On Linux/macOS
    source venv/bin/activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

#### Running the Application

When you run the application for the first time, it will automatically download the latest version of `sing-box.exe` for your operating system.

```bash
python main.py
```

## 📦 Building the Executable (EXE)

To build a standalone Windows executable (EXE) using PyInstaller:

1. Ensure all development prerequisites are met (like `pyinstaller`).
2. Simply run the `build.bat` script by double-clicking it.

The script will automatically handle all steps, and the final executable (`onix.exe`) will be created in the `dist` folder.

## 🖥️ User Interface and Usage

Onix features three main tabs: "Connection", "Settings", and "Routing".

### Connection Tab

This tab is for managing your servers and connections.

- **Server List (Left Panel):**
  - **Group Dropdown:** Displays your server groups.
  - **Search Bar:** Filter servers by name.
  - **Sortable Headers:** Click "Name" or "Ping" to sort the list.
  - **Server List:** Shows the servers within the selected group. Click on a server to select it. Right-click for more options.
  - **Start/Stop Buttons:** To start or stop the Sing-box connection.
  - **Status Bar:** Displays the current connection status, IP address, and latency.
- **Management Panel (Right Panel):**
  - **Subscription Management:** Manage and update your subscription links.
  - **Group Actions:** Ping all servers, perform URL tests, or cancel ongoing tests.
  - **Manual Add:**
    - **Add Single Server:** Manually add a server by pasting its share link.
    - **Scan QR Code from Screen:** Scans your screen for a QR code.
    - **Import WireGuard Config:** Add a WireGuard server by importing a `.conf` file.
  - **Log Panel:** Displays application logs with interactive filtering controls.

### Settings Tab

This tab is for configuring application settings.

- **Appearance Settings:** Change the display mode (Light, Dark) and color theme.
- **Network Settings:**
  - **Connection Mode:** Rule-Based or Global.
  - **DNS Servers:** Enter custom DNS servers.
  - **Bypass Rules:** Configure domains and IPs to bypass the proxy.
  - **Enable TUN Mode:** Enable system-wide proxying.
  - **TLS Fragment:** Configure TLS fragmentation options.
  - **Mux Settings:** Enable and configure multiplexing.
  - **Hysteria2 Settings:** Set default upload/download speeds.
- **Profile Management:** Import and export your entire application profile.
- **Updates:** Manually check for `sing-box` core updates.
- **About:** Shows application information.


### Routing Tab

This tab allows you to define custom rules to control how network traffic is routed. You can specify which traffic goes directly to the internet, which goes through the proxy, and which is blocked based on domain, IP, process, geosite, or geoip.

## 🤝 Contributing

We welcome contributions to Onix! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute, including our code style and commit message conventions.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.