# Onix - 一款现代化的 Sing-box GUI 客户端

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/network/members)

---

**语言:** [English](README.md) | [فارسی](README_fa.md) | [Русский](README_ru.md) | [简体中文](README_zh.md)

---

Onix 是一款为 Sing-box 设计的图形用户界面（GUI）客户端，旨在简化您的连接管理。它使用 `PySide6` 构建，为 Windows 提供了一个现代、功能丰富且用户友好的界面。

## ✨ 功能

- **广泛的协议支持:**
  - **标准协议:** VLESS, VMess, Shadowsocks, Trojan。
  - **现代协议:** **TUIC (v5)**, **Hysteria2**, 和 **WireGuard**。
- **自动核心管理:** Onix 会自动为您下载和管理最新的 `sing-box` 核心。
- **高级订阅管理:**
  - 添加、编辑和删除多个订阅链接。
  - 启用或禁用单个订阅。
  - 一键更新所有订阅以获取最新的服务器。
- **强大的服务器管理:**
  - 从订阅链接添加服务器。
  - 通过分享链接手动添加服务器。
  - 通过直接从屏幕上扫描二维码添加服务器。
  - 直接从 `.conf` 文件 **导入 WireGuard 配置**。
  - 将服务器组织成组以便更好地管理。
- **增强的 UI 和 UX:**
  - **搜索栏:** 按名称即时筛选您的服务器列表。
  - **可排序列:** 单击即可按名称或延迟对服务器进行排序。
  - **交互式日志面板:** 按级别（信息、警告、错误等）过滤日志，轻松调试问题。
  - **视觉反馈:** 在延迟测试期间，服务器旁边会显示“...”指示器。
- **连接测试与分析:**
  - 对您的服务器执行 TCP ping 和 URL 测试，以检查其性能。
  - 按 ping 结果对服务器进行排序，轻松找到最快的服务器。
- **系统集成 (Windows):**
  - 轻松启用或禁用系统范围的代理。
  - 在系统托盘中运行应用程序以进行隐蔽操作。
  - **TUN 模式:** 为所有应用程序启用系统范围的代理。
- **高级配置:**
  - **连接模式:** 在基于规则的代理模式和全局代理模式之间切换。
  - **可配置的 Mux:** 启用和配置多路复用（h2mux, smux, yamux）以提高性能。
  - **Hysteria2 带宽:** 为 Hysteria2 连接设置默认的上传和下载速度。
  - **自定义 DNS:** 设置自定义 DNS 服务器。
  - **绕过规则:** 配置要绕过代理的域名和 IP。
  - **自定义路由:** 定义高级自定义规则来控制网络流量的路由方式（例如，按域、IP、进程、geosite 或 geoip）。
- **配置文件管理:**
  - **导入/导出:** 轻松地将您的整个应用程序配置文件（包括服务器、订阅和设置）作为单个 JSON 文件导入和导出。

## 🚀 开始使用

### 下载并运行 (面向用户)

您无需安装 Python 即可使用 Onix。只需从 GitHub 上的 [Releases](https://github.com/AhmadAkd/onix/releases) 部分下载最新的可执行文件（EXE）。

1. 前往 [Releases 页面](https://github.com/AhmadAkd/onix/releases)。
2. 找到最新的版本并下载 `onix-windows-exe.zip` 文件。
3. 解压 ZIP 文件。
4. 运行 `onix.exe` 文件。

**注意:** `sing-box.exe` 文件由 Onix 自动下载和管理，您无需单独下载。

### 面向开发者

#### 先决条件

- Python 3.8+
- `pip` (Python 包安装程序)

#### 安装

1. 克隆仓库:

    ```bash
    git clone https://github.com/AhmadAkd/onix.git
    cd onix
    ```

2. 创建并激活虚拟环境:

    ```bash
    python -m venv venv
    # 在 Windows 上
    .\venv\Scripts\activate
    # 在 Linux/macOS 上
    source venv/bin/activate
    ```

3. 安装依赖项:

    ```bash
    pip install -r requirements.txt
    ```

#### 运行应用程序

首次运行应用程序时，它将自动为您的操作系统下载最新版本的 `sing-box.exe`。

```bash
python main.py
```

## 📦 构建可执行文件 (EXE)

要使用 PyInstaller 构建独立的 Windows 可执行文件（EXE）：

1. 确保满足所有开发先决条件（如 `pyinstaller`）。
2. 只需双击运行 `build.bat` 脚本即可。

该脚本将自动处理所有步骤，最终的可执行文件（`onix.exe`）将创建在 `dist` 文件夹中。

## 🖥️ 用户界面和用法

Onix 具有四个主要部分：“Connection”、“Routing”、“Logs” 和 “Settings”，可通过导航栏访问。

### Connection 视图

这是管理服务器和连接的主要视图。

- **顶部栏:** 包含用于组选择、服务器搜索、订阅管理和连接测试的控件。
- **服务器列表:** 显示所选组中的服务器。每个服务器都是一张卡片，显示其名称和延迟。上下文菜单提供编辑、删除和复制链接等操作。
- **状态栏 (底部):** 显示连接状态、IP、延迟、速度和主连接/断开按钮。

### Settings 视图

此视图用于配置应用程序设置。

- **外观设置:** 更改显示模式（亮色、暗色）和颜色主题。
- **网络设置:**
  - **连接模式:** 基于规则或全局。
  - **DNS 服务器:** 输入自定义 DNS 服务器。
  - **绕过规则:** 配置要绕过代理的域和 IP。
  - **启用 TUN 模式:** 启用系统范围的代理。
  - **Hysteria2 带宽:** 为 Hysteria2 连接设置默认的上传和下载速度。
- **配置文件管理:** 导入和导出您的整个应用程序配置文件。
- **更新:** 手动检查 `sing-box` 核心的更新。
- **关于:** 显示应用程序信息。

### Logs 视图

此视图显示来自应用程序和 `sing-box` 核心的实时日志。

- **搜索栏:** 快速搜索日志以查找特定消息或错误。
- **过滤控件:** 按级别（信息、警告、错误、调试）过滤日志，以专注于重要内容。
- **清除日志:** 一键清除面板中的所有日志消息。
- **复制日志:** 右键单击以复制所选文本或整行日志。

### Routing 选项卡

此视图允许您定义自定义规则来控制网络流量的路由方式。您可以根据域、IP、进程、geosite 或 geoip 指定哪些流量直接连接到互联网，哪些通过代理，哪些被阻止。

## 🤝 贡献

我们欢迎对 Onix 的贡献！有关如何贡献的指南，包括我们的代码风格和提交消息约定，请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 文件。

### 翻译 Onix

我们欢迎您为 Onix 贡献翻译，以支持更多语言！您可以这样提供帮助：

1.  **获取工具：** 您将需要 Qt Linguist，它是免费 Qt 工具的一部分。
2.  **找到您的语言文件：**
    *   进入 `translations/` 目录。
    *   找到您语言的文件，例如 `onix_fa.ts` (波斯语) 或 `onix_ru.ts` (俄语)。
    *   如果您的语言文件不存在，请提交一个 issue 来请求它，我们将为您创建初始文件。
3.  **翻译：**
    *   在 Qt Linguist 中打开 `.ts` 文件。
    *   为每个源文本在相应的字段中输入翻译，并将其标记为完成 (Ctrl+Enter)。
    *   保存您的更改。
4.  **提交您的贡献：**
    *   提交更新后的 `.ts` 文件。
    *   创建一个包含您更改的 Pull Request。您无需担心编译 `.qm` 文件；我们的构建过程会自动处理。

感谢您帮助 Onix 覆盖更广泛的用户！

## 📄 许可证

该项目根据 MIT 许可证授权。有关更多详细信息，请参阅 `LICENSE` 文件。
