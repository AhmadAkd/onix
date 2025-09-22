# Onix - Sing-box Client

Onix is a graphical user interface (GUI) client for Sing-box, designed to help you easily manage your Sing-box connections. Built with `customtkinter`, it offers a modern and user-friendly interface.

## Features

-   **Server Management:** Add and manage VLESS, Vmess, and Shadowsocks servers via subscription links or manually.
-   **Server Grouping:** Organize your servers into different groups for better management.
-   **Connection Testing:** Perform TCP pings and URL tests for your servers to check their performance and latency.
-   **System Proxy Settings:** Easily enable or disable Windows system proxy settings.
-   **Advanced Settings:** Configure custom DNS servers, bypass domains, and bypass IPs.
-   **Tray Mode:** Run the application in the system tray for discreet operation.
-   **Windows Support:** Specifically designed and optimized for the Windows operating system.

## Getting Started

### Download and Run (For Users)

You don't need Python installed to use Onix. Simply download the latest executable (EXE) from the [Releases](https://github.com/YOUR_USERNAME/onix/releases) section on GitHub.

1.  Go to the [Releases page](https://github.com/YOUR_USERNAME/onix/releases).
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
    git clone https://github.com/YOUR_USERNAME/onix.git
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

## Building the Executable (EXE)

To build a standalone Windows executable (EXE) using PyInstaller:

1.  Ensure PyInstaller is installed (`pip install pyinstaller`).
2.  Make sure `sing-box.exe` is located next to `main.py`.
3.  Run the following command:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "sing-box.exe;." main.py
    ```
    The executable will be created in the `dist` folder.

## Contributing

We welcome contributions to Onix! To ensure a smooth and collaborative development process, please follow these guidelines:

### How to Contribute

1.  **Fork the Repository:** Start by forking the Onix repository to your GitHub account.
2.  **Clone Your Fork:** Clone your forked repository to your local machine.
    ```bash
    git clone https://github.com/YOUR_USERNAME/onix.git
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

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---
**Note:** Please replace `YOUR_USERNAME` in the GitHub links with your actual GitHub username.
