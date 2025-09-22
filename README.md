# Onix - Sing-box Client

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/network/members)

---

**Languages:** [English](README.md) | [فارسی](README_fa.md) | [Русский](README_ru.md) | [简体中文](README_zh.md)

---

Onix is a graphical user interface (GUI) client for Sing-box, designed to help you easily manage your Sing-box connections. Built with `customtkinter`, it offers a modern and user-friendly interface.

## ✨ Features

-   **Server Management:** Add and manage VLESS, Vmess, and Shadowsocks servers via subscription links or manually.
-   **Server Grouping:** Organize your servers into different groups for better management.
-   **Connection Testing:** Perform TCP pings and URL tests for your servers to check their performance and latency.
-   **System Proxy Settings:** Easily enable or disable Windows system proxy settings.
-   **Advanced Settings:** Configure custom DNS servers, bypass domains, and bypass IPs.
-   **Tray Mode:** Run the application in the system tray for discreet operation.
-   **Windows Support:** Specifically designed and optimized for the Windows operating system.

## 🚀 Getting Started

### Download and Run (For Users)

You don't need Python installed to use Onix. Simply download the latest executable (EXE) from the [Releases](https://github.com/AhmadAkd/onix/releases) section on GitHub.

1.  Go to the [Releases page](https://github.com/AhmadAkd/onix/releases).
2.  Find the latest release and download the `onix-windows-exe.zip` file.
3.  Extract the ZIP file.
4.  Run the `main.exe` file.

**Note:** The `sing-box.exe` file is automatically bundled with `main.exe`, so you do not need to download it separately.

### For Developers

#### Prerequisites

-   Python 3.8+
-   `pip` (Python package installer)

#### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/AhmadAkd/onix.git
    cd onix
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On Linux/macOS
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Download the `sing-box.exe` file. You can get it from the [official Sing-box Releases page](https://github.com/SagerNet/sing-box/releases). Download the `sing-box-X.Y.Z-windows-amd64.zip` file, extract `sing-box.exe` from it, and place it next to your `main.py` file.

#### Running the Application

```bash
python main.py
```

## 📦 Building the Executable (EXE)

To build a standalone Windows executable (EXE) using PyInstaller:

1.  Ensure PyInstaller is installed (`pip install pyinstaller`).
2.  Make sure `sing-box.exe` is located next to `main.py`.
3.  Run the following command:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "sing-box.exe;." main.py
    ```
    The executable will be created in the `dist` folder.

## 🖥️ User Interface and Usage

Onix features two main tabs: "Connection" and "Settings".

### Connection Tab

This tab is for managing your servers and connections.

-   **Server List (Left Panel):**
    *   **Group Dropdown:** Displays your server groups. Select a group to view its servers.
    *   **Server List:** Shows the servers within the selected group. Click on a server to select it.
    *   **Start/Stop Buttons:** To start or stop the Sing-box connection with the selected server.
    *   **Status Bar:** Displays the current connection status, IP address, and latency.
-   **Management Panel (Right Panel):**
    *   **Subscription Management:**
        *   **Subscription Link:** Enter your server subscription link here.
        *   **Group Name (Optional):** Enter a name for the new server group.
        *   **Update Button:** To update the server list from the subscription link.
    *   **Group Actions:**
        *   **Ping Group:** Performs a TCP ping test for all servers in the current group.
        *   **URL Test Group:** Performs a URL test for all servers in the current group (this can be time-consuming).
        *   **Sort by Ping:** Sorts the servers by their ping latency.
        *   **URL Test (Active):** Performs a URL test on the currently active connection.
    *   **Manual Add:**
        *   **Add Single Server:** Manually add a server by pasting its link.
    *   **Log Textbox:** Displays messages related to application activities.

### Settings Tab

This tab is for configuring application settings.

-   **Appearance Settings:**
    *   **Appearance Mode:** Changes the display mode (Light, Dark, System).
    *   **Color Theme:** Changes the application's color theme (requires app restart for full effect).
-   **Network Settings:**
    *   **Connection Mode:** Sets the connection mode (Rule-Based or Global).
    *   **DNS Servers:** Enter custom DNS servers (comma-separated).
    *   **Bypass Domains:** Enter domains that should bypass the proxy (comma-separated).
    *   **Bypass IPs:** Enter IP addresses that should bypass the proxy (comma-separated).

## 🤝 Contributing

We welcome contributions to Onix! To ensure a smooth and collaborative development process, please follow these guidelines:

### How to Contribute

1.  **Fork the Repository:** Start by forking the Onix repository to your GitHub account.
2.  **Clone Your Fork:** Clone your forked repository to your local machine.
    ```bash
    git clone https://github.com/AhmadAkd/onix.git
    cd onix
    ```
3.  **Create a New Branch:** Create a new branch for your feature or bug fix. Use a descriptive name (e.g., `feature/add-new-protocol`, `bugfix/connection-issue`).
    ```bash
    git checkout -b feature/your-feature-name
    ```
4.  **Make Your Changes:** Implement your changes, ensuring they adhere to the project's coding style and conventions.
5.  **Test Your Changes:** Thoroughly test your changes to ensure they work as expected and do not introduce new bugs. If applicable, add new unit tests.
6.  **Commit Your Changes:** Write clear and concise commit messages. Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification (e.g., `feat: Add new feature`, `fix: Resolve bug`).
    ```bash
    git commit -m "feat: Briefly describe your changes"
    ```
7.  **Push to Your Fork:** Push your local branch to your forked repository on GitHub.
    ```bash
    git push origin feature/your-feature-name
    ```
8.  **Create a Pull Request (PR):** Go to the original Onix repository on GitHub and create a new Pull Request from your forked branch.
    *   Provide a clear title and detailed description of your changes.
    *   Reference any related issues.
    *   Ensure your PR passes all CI checks.

### Code Style

-   Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style.
-   Use clear and descriptive variable/function names.
-   Add comments where necessary to explain complex logic.

### Reporting Bugs

If you find a bug, please open an issue on GitHub. Provide as much detail as possible, including:

-   A clear and concise description of the bug.
-   Steps to reproduce the behavior.
-   Expected behavior.
-   Screenshots or error messages (if applicable).
-   Your operating system and Onix version.

### Feature Requests

We welcome ideas for new features! Please open an issue on GitHub to suggest new features. Describe:

-   The problem your feature solves.
-   How you envision the feature working.
-   Any potential benefits or use cases.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.