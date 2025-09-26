# Onix - Sing-box Client

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/network/members)

---

**Languages:** [English](README.md) | [فارسی](README_fa.md) | [Русский](README_ru.md) | [简体中文](README_zh.md)

---

Onix is a graphical user interface (GUI) client for Sing-box, designed to help you easily manage your Sing-box connections. Built with `customtkinter`, it offers a modern and user-friendly interface.

## ✨ Features

- **Multi-Protocol Support:** Add and manage VLESS, Vmess, Shadowsocks, and Trojan servers.
- **Automatic Updates:** Onix automatically downloads the latest `sing-box` core for you.
- **Subscription Management:**
    - Add, edit, and delete multiple subscription links.
    - Enable or disable individual subscriptions.
    - Update all subscriptions with a single click to fetch the latest servers.
- **Server Management:**
    - Add servers from subscription links.
    - Add servers manually via share links.
    - Add servers by scanning QR codes directly from your screen.
    - Organize servers into groups for better management.
- **Connection Testing & Analysis:**
    - Perform TCP pings and URL tests for your servers to check their performance and latency.
    - Sort servers by ping results to easily find the fastest one.
- **System Integration (Windows):**
    - Easily enable or disable the system-wide proxy.
    - Run the application in the system tray for discreet operation.
    - **TUN Mode:** Enable system-wide proxying for all applications.
- **Advanced Configuration:**
    - **Connection Mode:** Switch between Rule-Based and Global proxy modes.
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
  - **Group Dropdown:** Displays your server groups. Select a group to view its servers.
  - **Server List:** Shows the servers within the selected group. Click on a server to select it. Right-click for more options like ping, edit, and delete.
  - **Start/Stop Buttons:** To start or stop the Sing-box connection with the selected server.
  - **Status Bar:** Displays the current connection status, IP address, and latency.
- **Management Panel (Right Panel):**
  - **Subscription Management:**
    - **Manage Subscriptions:** Opens a window to add, edit, delete, and enable/disable your subscription links.
    - **Update All Subscriptions:** Updates the server list from all your enabled subscription links.
  - **Group Actions:**
    - **Ping Group:** Performs a TCP ping test for all servers in the current group.
    - **URL Test Group:** Performs a URL test for all servers in the current group (this can be time-consuming).
    - **Sort by Ping:** Sorts the servers by their ping latency.
    - **URL Test (Active):** Performs a URL test on the currently active connection.
  - **Manual Add:**
    - **Add Single Server:** Manually add a server by pasting its share link (e.g., `vless://...`).
    - **Scan QR Code from Screen:** Scans your screen for a QR code and automatically adds the server.
  - **Log Textbox:** Displays messages related to application activities.

### Settings Tab

This tab is for configuring application settings.

- **Appearance Settings:**
  - **Appearance Mode:** Changes the display mode (Light, Dark, System).
  - **Color Theme:** Changes the application's color theme (requires app restart for full effect).
- **Network Settings:**
  - **Connection Mode:** Sets the connection mode (Rule-Based or Global).
  - **DNS Servers:** Enter custom DNS servers (comma-separated).
  - **Bypass Domains:** Enter domains that should bypass the proxy (comma-separated).
  - **Bypass IPs:** Enter IP addresses that should bypass the proxy (comma-separated).
  - **Enable TUN Mode:** Enable system-wide proxying for all applications (requires restart).
- **Profile Management:**
    - **Import Profile:** Import all your settings and servers from a previously exported JSON file.
    - **Export Profile:** Export all your current settings and servers to a JSON file for backup or sharing.
- **Updates:**
    - **Check for sing-box Updates:** Manually check for and download the latest version of the `sing-box` core.
- **About:**
    - **About Onix:** Shows information about the application and a link to the GitHub releases page.


### Routing Tab

This tab allows you to define custom rules to control how network traffic is routed. You can specify which traffic goes directly to the internet, which goes through the proxy, and which is blocked.

- **Rule List:** Displays all the custom routing rules you have added.
- **Add Rule:** Opens a dialog to create a new rule.
  - **Rule Type:** Choose from `domain`, `ip`, `process`, `geosite`, or `geoip`.
  - **Value:** The value to match (e.g., `google.com`, `1.1.1.1`, `iran`).
  - **Action:** Choose whether to `direct`, `proxy`, or `block` the matching traffic.
- **Edit/Delete Rule:** Modify or remove existing rules.
- **Save/Load Rules:** Save your current rules to the settings file or load them back.

## 🤝 Contributing

We welcome contributions to Onix! To ensure a smooth and collaborative development process, please follow these guidelines:

### How to Contribute

1. **Fork the Repository:** Start by forking the Onix repository to your GitHub account.
2. **Clone Your Fork:** Clone your forked repository to your local machine.

    ```bash
    git clone https://github.com/AhmadAkd/onix.git
    cd onix
    ```

3. **Create a New Branch:** Create a new branch for your feature or bug fix. Use a descriptive name (e.g., `feature/add-new-protocol`, `bugfix/connection-issue`).

    ```bash
    git checkout -b feature/your-feature-name
    ```

4. **Make Your Changes:** Implement your changes, ensuring they adhere to the project's coding style and conventions.
5. **Test Your Changes:** Thoroughly test your changes to ensure they work as expected and do not introduce new bugs. If applicable, add new unit tests.
6. **Commit Your Changes:** Write clear and concise commit messages. Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification (e.g., `feat: Add new feature`, `fix: Resolve bug`).

    ```bash
    git commit -m "feat: Briefly describe your changes"
    ```

7. **Push to Your Fork:** Push your local branch to your forked repository on GitHub.

    ```bash
    git push origin feature/your-feature-name
    ```

8. **Create a Pull Request (PR):** Go to the original Onix repository on GitHub and create a new Pull Request from your forked branch.
    - Provide a clear title and detailed description of your changes.
    - Reference any related issues.
    - Ensure your PR passes all CI checks.

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style.
- Use clear and descriptive variable/function names.
- Add comments where necessary to explain complex logic.

### Commit Message Convention

We use the **Conventional Commits** specification for our commit messages. This leads to more readable messages that are easy to follow and allows us to automate the generation of changelogs.

Each commit message consists of a **header**, a **body**, and a **footer**.

```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

**Type**

The type must be one of the following:

- **feat**: A new feature for the user.
- **fix**: A bug fix for the user.
- **docs**: Changes to documentation.
- **style**: Code style changes (formatting, white-space, etc.).
- **refactor**: A code change that neither fixes a bug nor adds a feature.
- **perf**: A code change that improves performance.
- **test**: Adding missing tests or correcting existing tests.
- **build**: Changes that affect the build system or external dependencies.
- **ci**: Changes to our CI configuration files and scripts.
- **chore**: Other changes that don't modify source or test files.

**Examples**

- `feat(ui): Add a new 'About' window`
- `fix(proxy): Correctly handle system proxy disabling on exit`
- `docs: Update contribution guidelines with commit conventions`
- `refactor(settings): Simplify settings loading logic`
- `ci: Automate changelog generation on release`

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style.
- Use clear and descriptive variable/function names.
- Add comments where necessary to explain complex logic.

### Reporting Bugs

If you find a bug, please open an issue on GitHub. Provide as much detail as possible, including:

- A clear and concise description of the bug.
- Steps to reproduce the behavior.
- Expected behavior.
- Screenshots or error messages (if applicable).
- Your operating system and Onix version.

### Feature Requests

We welcome ideas for new features! Please open an issue on GitHub to suggest new features. Describe:

- The problem your feature solves.
- How you envision the feature working.
- Any potential benefits or use cases.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
