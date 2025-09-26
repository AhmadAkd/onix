# Onix - 一款现代化的 Sing-box GUI 客户端

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/network/members)

---

**语言:** [English](README.md) | [فارسی](README_fa.md) | [Русский](README_ru.md) | [简体中文](README_zh.md)

---

Onix 是一款为 Sing-box 设计的图形用户界面（GUI）客户端，旨在简化您的连接管理。它使用 `customtkinter` 构建，为 Windows 提供了一个现代、功能丰富且用户友好的界面。

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

Onix 具有三个主要选项卡：“Connection”、“Settings” 和 “Routing”。

### Connection 选项卡

此选项卡用于管理您的服务器和连接。

- **服务器列表 (左侧面板):**
  - **组下拉菜单:** 显示您的服务器组。
  - **搜索栏:** 按名称筛选服务器。
  - **可排序列标题:** 单击“Name”或“Ping”以对列表进行排序。
  - **服务器列表:** 显示所选组中的服务器。单击服务器以选择它。右键单击以获取更多选项。
  - **启动/停止按钮:** 启动或停止 Sing-box 连接。
  - **状态栏:** 显示当前连接状态、IP 地址和延迟。
- **管理面板 (右侧面板):**
  - **订阅管理:** 管理和更新您的订阅链接。
  - **组操作:** Ping 所有服务器、执行 URL 测试或取消正在进行的测试。
  - **手动添加:**
    - **添加单个服务器:** 通过粘贴其分享链接手动添加服务器。
    - **从屏幕扫描二维码:** 从屏幕上扫描二维码。
    - **导入 WireGuard 配置:** 通过导入 `.conf` 文件添加 WireGuard 服务器。
  - **日志面板:** 显示带有交互式过滤控件的应用程序日志。

### Settings 选项卡

此选项卡用于配置应用程序设置。

- **外观设置:** 更改显示模式（亮色、暗色）和颜色主题。
- **网络设置:**
  - **连接模式:** 基于规则或全局。
  - **DNS 服务器:** 输入自定义 DNS 服务器。
  - **绕过规则:** 配置要绕过代理的域和 IP。
  - **启用 TUN 模式:** 启用系统范围的代理。
  - **TLS 片段:** 配置 TLS 分片选项。
  - **Mux 设置:** 启用和配置多路复用。
  - **Hysteria2 设置:** 设置默认的上传/下载速度。
- **配置文件管理:** 导入和导出您的整个应用程序配置文件。
- **更新:** 手动检查 `sing-box` 核心的更新。
- **关于:** 显示应用程序信息。


### Routing 选项卡

此选项卡允许您定义自定义规则来控制网络流量的路由方式。您可以根据域、IP、进程、geosite 或 geoip 指定哪些流量直接连接到互联网，哪些通过代理，哪些被阻止。

## 🤝 贡献

我们欢迎对 Onix 的贡献！有关如何贡献的指南，包括我们的代码风格和提交消息约定，请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 文件。

## 📄 许可证

该项目根据 MIT 许可证授权。有关更多详细信息，请参阅 `LICENSE` 文件。