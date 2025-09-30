# Onix - A Modern GUI Client for Sing-box

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/network/members)

---

**Languages:** [English](README.md) | [فارسی](README_fa.md) | [Русский](README_ru.md) | [简体中文](README_zh.md)

---

Onix is a graphical user interface (GUI) client for Sing-box, designed to simplify managing your connections. Built with `PySide6`, it offers a modern, feature-rich, and user-friendly interface for Windows.

## ✨ Features

### 🚀 Core Features
- **Extensive Protocol Support:**
  - **Standard Protocols:** VLESS, VMess, Shadowsocks, Trojan.
  - **Modern Protocols:** **TUIC (v5)**, **Hysteria2**, and **WireGuard**.
- **Automatic Core Management:** Onix automatically downloads and manages the latest `sing-box` core for you.
- **Advanced Subscription Management:**
  - Add, edit, and delete multiple subscription links.
  - Enable or disable individual subscriptions.
  - Update all subscriptions with a single click to fetch the latest servers.

### 🖥️ Server Management
- **Powerful Server Management:**
  - Add servers from subscription links.
  - Add servers manually via share links.
  - Add servers by scanning QR codes directly from your screen.
  - **Import WireGuard configs** directly from `.conf` files.
  - Organize servers into groups for better management.
- **Connection Testing & Analysis:**
  - Perform TCP pings and URL tests for your servers to check their performance.
  - **Real-time Speed Test** with detailed analytics and monitoring.
  - Sort servers by ping results to easily find the fastest one.
  - **Auto-failover** for automatic server switching on connection failure.

### 🎨 Enhanced UI & UX
- **Modern Interface:** Clean, responsive design with RTL support.
- **Search & Filter:** Instantly filter your server list by name.
- **Sortable Columns:** Sort servers by name or ping latency with a single click.
- **Interactive Log Panel:** Filter logs by level (Info, Warning, Error, etc.) to easily debug issues.
- **Visual Feedback:** See "..." indicators next to servers during latency tests.
- **Custom Themes:** Multiple themes with dark/light mode support.
- **Settings Search:** Quick search functionality across all settings.
- **Settings Presets:** Pre-configured settings (Balanced, Performance, Security, Privacy).

### 🔒 Advanced Security & Privacy
- **Kill Switch:** Automatic connection protection on proxy failure.
- **DNS Leak Protection:** Prevent DNS leaks and ensure privacy.
- **Certificate Pinning:** Enhanced security for TLS connections.
- **IPv6 Leak Protection:** Comprehensive IPv6 leak prevention.
- **Privacy Controls:** Comprehensive data protection and privacy settings.
- **Data Collection Controls:** Disable telemetry, crash reports, and usage statistics.

### ⚡ Performance & Monitoring
- **Real-time Statistics:** Live monitoring of connection performance.
- **Performance Analytics:** Detailed performance monitoring and diagnostics.
- **Connection Multiplexing:** Advanced multiplexing for improved performance.
- **Bandwidth Limiting:** Upload/download speed controls.
- **Performance Dashboard:** Visual performance metrics and analytics.

### 🔧 Advanced Configuration
- **Connection Mode:** Switch between Rule-Based and Global proxy modes.
- **Configurable Muxing:** Enable and configure multiplexing (h2mux, smux, yamux) to improve performance.
- **Hysteria2 Bandwidth:** Set default upload and download speeds for Hysteria2 connections.
- **Custom DNS:** Set custom DNS servers.
- **Bypass Rules:** Configure domains and IPs to bypass the proxy.
- **Custom Routing:** Define advanced, custom rules to control how network traffic is routed (e.g., by domain, IP, process, geosite, or geoip).

### 🌐 System Integration
- **System Integration (Windows):**
  - Easily enable or disable the system-wide proxy.
  - Run the application in the system tray for discreet operation.
  - **TUN Mode:** Enable system-wide proxying for all applications.
- **Browser Integration:** Seamless browser integration capabilities.
- **Keyboard Shortcuts:** Quick access to common functions.
- **System Notifications:** Important event notifications.

### 👥 Multi-User & Backup
- **Multi-user Support:** User management and profile system.
- **Auto-backup:** Automatic configuration backup and restore.
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

Onix features four main sections: "Connection", "Routing", "Logs", and "Settings", accessible via a navigation rail.

### Connection View

This is the main view for managing your servers and connections.

- **Top Bar:** Contains controls for group selection, server search, subscription management, and connection testing.
- **Server List:** Displays servers in the selected group. Each server is a card showing its name and ping. A context menu provides actions like edit, delete, and copy link.
- **Status Bar (Bottom):** Shows connection status, IP, latency, speed, and the main connect/disconnect button.

### Settings View

This view is for configuring application settings.

- **Appearance Settings:** Change the display mode (Light, Dark) and color theme.
- **Network Settings:**
  - **Connection Mode:** Rule-Based or Global.
  - **DNS Servers:** Enter custom DNS servers.
  - **Bypass Rules:** Configure domains and IPs to bypass the proxy.
  - **Enable TUN Mode:** Enable system-wide proxying.
  - **Hysteria2 Bandwidth:** Set default upload and download speeds for Hysteria2 connections.
- **Profile Management:** Import and export your entire application profile.
- **Updates:** Manually check for `sing-box` core updates.
- **About:** Shows application information.

### Logs View

This view displays real-time logs from the application and the `sing-box` core.

- **Search Bar:** Quickly search through logs to find specific messages or errors.
- **Filter Controls:** Filter logs by level (Info, Warning, Error, Debug) to focus on what matters.
- **Clear Logs:** Clear all log messages from the panel with a single click.
- **Copy Logs:** Right-click to copy selected text or the entire log line.

### Routing Tab

This view allows you to define custom rules to control how network traffic is routed. You can specify which traffic goes directly to the internet, which goes through the proxy, and which is blocked based on domain, IP, process, geosite, or geoip.

## 🤝 Contributing

We welcome contributions to Onix! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute, including our code style and commit message conventions.

### Translating Onix

We welcome contributions to translate Onix into more languages! Here’s how you can help:

1. **Get the Tools:** You will need [Qt Linguist](https://doc.qt.io/qt-6/qtlinguist-index.html), which is part of the free Qt tools.
2. **Find Your Language File:**
    - Go to the `translations/` directory.
    - Find the file for your language, like `onix_fa.ts` for Persian or `onix_ru.ts` for Russian.
    - If your language file doesn't exist, please open an issue to request it, and we'll create the initial file for you.
3. **Translate:**
    - Open the `.ts` file in Qt Linguist.
    - For each source text, enter the translation in the corresponding field and mark it as complete (Ctrl+Enter).
    - Save your changes.
4. **Submit Your Contribution:**
    - Commit the updated `.ts` file.
    - Create a Pull Request with your changes. You don't need to worry about compiling the `.qm` files; our build process handles that.

Thank you for helping make Onix accessible to more users!

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
