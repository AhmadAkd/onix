# Onix - Sing-box 客户端

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/network/members)

---

**语言:** [English](README.md) | [فارسی](README_fa.md) | [Русский](README_ru.md) | [简体中文](README_zh.md)

---

Onix 是一个 Sing-box 的图形用户界面 (GUI) 客户端，旨在帮助您轻松管理 Sing-box 连接。它使用 `customtkinter` 构建，提供了一个现代且用户友好的界面。

## ✨ 功能

-   **服务器管理：** 通过订阅链接或手动添加和管理 VLESS、Vmess 和 Shadowsocks 服务器。
-   **服务器分组：** 将您的服务器组织成不同的组，以便更好地管理。
-   **连接测试：** 对您的服务器执行 TCP ping 和 URL 测试，以检查其性能和延迟。
-   **系统代理设置：** 轻松启用或禁用 Windows 系统代理设置。
-   **高级设置：** 配置自定义 DNS 服务器、绕过域名和绕过 IP。
-   **托盘模式：：** 在系统托盘中运行应用程序，以便隐秘操作。
-   **Windows 支持：** 专为 Windows 操作系统设计和优化。

## 🚀 入门

### 下载和运行（针对用户）

您无需安装 Python 即可使用 Onix。只需从 GitHub 上的 [Releases](https://github.com/AhmadAkd/onix/releases) 部分下载最新的可执行文件 (EXE)。

1.  转到 [Releases 页面](https://github.com/AhmadAkd/onix/releases)。
2.  找到最新版本并下载 `onix-windows-exe.zip` 文件。
3.  解压 ZIP 文件。
4.  运行 `main.exe` 文件。

**注意：** `sing-box.exe` 文件已自动与 `main.exe` 捆绑，因此您无需单独下载。

### 针对开发者

#### 先决条件

-   Python 3.8+
-   `pip` (Python 包安装程序)

#### 安装

1.  克隆仓库：
    ```bash
    git clone https://github.com/AhmadAkd/onix.git
    cd onix
    ```
2.  创建并激活虚拟环境：
    ```bash
    python -m venv venv
    # 在 Windows 上
    .\venv\Scripts\activate
    # 在 Linux/macOS 上
    source venv/bin/activate
    ```
3.  安装依赖项：
    ```bash
    pip install -r requirements.txt
    ```
4.  下载 `sing-box.exe` 文件。您可以从 [Sing-box 官方发布页面](https://github.com/SagerNet/sing-box/releases) 获取。下载 `sing-box-X.Y.Z-windows-amd64.zip` 文件，从中提取 `sing-box.exe` 并将其放在 `main.py` 文件旁边。

#### 运行应用程序

```bash
python main.py
```

## 📦 构建可执行文件 (EXE)

要使用 PyInstaller 构建独立的 Windows 可执行文件 (EXE)：

1.  确保已安装 PyInstaller (`pip install pyinstaller`)。
2.  确保 `sing-box.exe` 位于 `main.py` 旁边。
3.  运行以下命令：
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "sing-box.exe;." main.py
    ```
    可执行文件将在 `dist` 文件夹中创建。

## 🖥️ 用户界面和使用

Onix 具有两个主要选项卡：“连接”和“设置”。

### 连接选项卡

此选项卡用于管理您的服务器和连接。

-   **服务器列表（左侧面板）：**
    *   **组下拉菜单：** 显示您的服务器组。选择一个组以查看其服务器。
    *   **服务器列表：** 显示所选组中的服务器。单击服务器以选择它。
    *   **启动/停止按钮：** 用于启动或停止与所选服务器的 Sing-box 连接。
    *   **状态栏：：** 显示当前连接状态、IP 地址和延迟。
-   **管理面板（右侧面板）：**
    *   **订阅管理：**
        *   **订阅链接：** 在此处输入您的服务器订阅链接。
        *   **组名称（可选）：** 输入新服务器组的名称。
        *   **更新按钮：** 用于从订阅链接更新服务器列表。
    *   **组操作：**
        *   **Ping 组：** 对当前组中的所有服务器执行 TCP ping 测试。
        *   **URL 测试组：** 对当前组中的所有服务器执行 URL 测试（这可能很耗时）。
        *   **按 Ping 排序：** 按 ping 延迟对服务器进行排序。
        *   **URL 测试（活动）：：** 对当前活动连接执行 URL 测试。
    *   **手动添加：**
        *   **添加单个服务器：** 通过粘贴其链接手动添加服务器。
    *   **日志文本框：** 显示与应用程序活动相关的消息。

### 设置选项卡

此选项卡用于配置应用程序设置。

-   **外观设置：**
    *   **外观模式：** 更改显示模式（浅色、深色、系统）。
    *   **颜色主题：** 更改应用程序的颜色主题（需要重新启动应用程序才能完全生效）。
-   **网络设置：**
    *   **连接模式：** 设置连接模式（基于规则或全局）。
    *   **DNS 服务器：** 输入自定义 DNS 服务器（逗号分隔）。
    *   **绕过域名：** 输入应绕过代理的域名（逗号分隔）。
    *   **绕过 IP：** 输入应绕过代理的 IP 地址（逗号分隔）。

## 🤝 贡献

我们欢迎对 Onix 的贡献！为确保流畅和协作的开发过程，请遵循以下准则：

### 如何贡献

1.  **Fork 仓库：** 首先将 Onix 仓库 Fork 到您的 GitHub 帐户。
2.  **克隆您的 Fork：** 将您 Fork 的仓库克隆到您的本地计算机。
    ```bash
    git clone https://github.com/AhmadAkd/onix.git
    cd onix
    ```
3.  **创建新分支：** 为您的功能或错误修复创建一个新分支。使用描述性名称（例如，`feature/add-new-protocol`、`bugfix/connection-issue`）。
    ```bash
    git checkout -b feature/your-feature-name
    ```
4.  **进行更改：** 实现您的更改，确保它们符合项目的编码风格和约定。
5.  **测试您的更改：** 彻底测试您的更改，以确保它们按预期工作并且不会引入新错误。如果适用，添加新的单元测试。
6.  **提交您的更改：** 编写清晰简洁的提交消息。遵循 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 规范（例如，`feat: Add new feature`、`fix: Resolve bug`）。
    ```bash
    git commit -m "feat: 简要描述您的更改"
    ```
7.  **推送到您的 Fork：** 将您的本地分支推送到 GitHub 上的 Fork 仓库。
    ```bash
    git push origin feature/your-feature-name
    ```
8.  **创建拉取请求 (PR)：** 转到 GitHub 上的原始 Onix 仓库，并从您的 Fork 分支创建一个新的拉取请求。
    *   提供清晰的标题和详细的更改描述。
    *   引用任何相关问题。
    *   确保您的 PR 通过所有 CI 检查。

### 代码风格

-   遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 的 Python 代码风格。
-   使用清晰且描述性的变量/函数名称。
-   在必要时添加注释以解释复杂的逻辑。

### 报告错误

如果您发现错误，请在 GitHub 上打开一个 issue。提供尽可能多的详细信息，包括：

-   清晰简洁的错误描述。
-   重现行为的步骤。
-   预期行为。
-   屏幕截图或错误消息（如果适用）。
-   您的操作系统和 Onix 版本。

### 功能请求

我们欢迎新功能的想法！请在 GitHub 上打开一个 issue 以建议新功能。描述：

-   您的功能解决的问题。
-   您设想的功能如何工作。
-   任何潜在的好处或用例。

## 📄 许可证

本项目根据 MIT 许可证获得许可。有关更多详细信息，请参阅 `LICENSE` 文件。