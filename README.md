# Sing-box Client

A graphical user interface (GUI) for the [sing-box](https://github.com/SagerNet/sing-box) universal proxy tool, built with Python and customtkinter.

This client allows you to easily manage and switch between different server configurations from subscription links.

![Screenshot](placeholder.png) <!-- Add a screenshot of the application -->

## Features

-   **Subscription Management**: Update server lists from subscription links.
-   **VLESS Protocol Support**: Parses `vless://` links.
-   **Server Grouping**: Automatically groups servers based on their names.
-   **Latency Testing**:
    -   Test servers via TCP Ping.
    -   Test real-world latency with a URL test.
-   **System Proxy**: Automatically sets/unsets the Windows system proxy.
-   **System Tray**: Can be minimized to the system tray.
-   **Light/Dark Mode**: Supports system appearance settings.

## Prerequisites

-   Python 3.8+
-   The `sing-box.exe` executable in the project's root directory. You can download the latest version from the [official releases](https://github.com/SagerNet/sing-box/releases).

## Installation & Usage

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Ahmad/SingboxClient.git
    cd SingboxClient
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # Install requirements
    pip install -r requirements.txt
    ```

3.  **Download `sing-box.exe`:**
    Make sure you have `sing-box.exe` in the root folder of the project.

4.  **Run the application:**
    ```bash
    python main.py
    ```

## How to Contribute

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

