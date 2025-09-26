# Onix - Sing-box 客户端

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/AhmadAkd/onix?style=social)](https://github.com/AhmadAkd/onix/network/members)

---

**语言:** [English](README.md) | [فارسی](README_fa.md) | [Русский](README_ru.md) | [简体中文](README_zh.md)

---

Onix 是一个 Sing-box 的图形用户界面 (GUI) 客户端，旨在帮助您轻松管理 Sing-box 连接。它使用 `customtkinter` 构建，提供了一个现代且用户友好的界面。

## ✨ 功能

- **服务器管理：** 通过订阅链接或手动添加和管理 VLESS、Vmess 和 Shadowsocks 服务器。
- **服务器分组：** 将您的服务器组织成不同的组，以便更好地管理。
- **连接测试：** 对您的服务器执行 TCP ping 和 URL 测试，以检查其性能和延迟。
- **系统代理设置：** 轻松启用或禁用 Windows 系统代理设置。
- **高级设置：** 配置自定义 DNS 服务器、绕过域名和绕过 IP。
- **自定义路由规则：** 添加、编辑和删除自定义路由规则，以实现高级流量控制。
- **托盘模式：** 在系统托盘中运行应用程序，以便隐秘操作。
- **Windows 支持：** 专为 Windows 操作系统设计和优化。

## 🚀 入门

### 下载和运行（针对用户）

您无需安装 Python 即可使用 Onix。只需从 GitHub 上的 [Releases](https://github.com/AhmadAkd/onix/releases) 部分下载最新的可执行文件 (EXE)。

1. 转到 [Releases 页面](https://github.com/AhmadAkd/onix/releases)。
2. 找到最新版本并下载 `onix-windows-exe.zip` 文件。
3. 解压 ZIP 文件。
4. 运行 `onix.exe` 文件。

**注意：** `sing-box.exe` 文件已自动与 `onix.exe` 捆绑，因此您无需单独下载。

### 针对开发者

#### 先决条件

- Python 3.8+
- `pip` (Python 包安装程序)

#### 安装

1. 克隆仓库：

    ```bash
    git clone https://github.com/AhmadAkd/onix.git
    cd onix
    ```

2. 创建并激活虚拟环境：

    ```bash
    python -m venv venv
    # 在 Windows 上
    .\venv\Scripts\activate
    # 在 Linux/macOS 上
    source venv/bin/activate
    ```

3. 安装依赖项：

    ```bash
    pip install -r requirements.txt
    ```

4. 下载 `sing-box.exe` 文件。您可以从 [Sing-box 官方发布页面](https://github.com/SagerNet/sing-box/releases) 获取。下载 `sing-box-X.Y.Z-windows-amd64.zip` 文件，从中提取 `sing-box.exe` 并将其放在 `main.py` 文件旁边。

#### 运行应用程序

```bash
python main.py
```

## 📦 构建可执行文件 (EXE)

要使用 PyInstaller 构建独立的 Windows 可执行文件 (EXE)：

1. 确保已安装 PyInstaller (`pip install pyinstaller`)。
2. 确保 `sing-box.exe` 位于 `main.py` 旁边。
3. 对于手动构建，请在根目录中创建一个 `version.txt` 文件，并在其中写入 `dev`。
3. 运行以下命令：

    ```bash
    pyinstaller --noconfirm --onefile --windowed --name onix --add-data "sing-box.exe;." --add-data "version.txt;." --icon="assets/icon.ico" main.py
    ```

    可执行文件 (`onix.exe`) 将在 `dist` 文件夹中创建。

## 🖥️ 用户界面和使用

Onix 具有两个主要选项卡：“连接”和“设置”。

### 连接选项卡

此选项卡用于管理您的服务器和连接。

- **服务器列表（左侧面板）：**
  - **组下拉菜单：** 显示您的服务器组。选择一个组以查看其服务器。
  - **服务器列表：** 显示所选组中的服务器。单击服务器以选择它。
  - **启动/停止按钮：** 用于启动或停止与所选服务器的 Sing-box 连接。
  - **状态栏：：** 显示当前连接状态、IP 地址和延迟。
- **管理面板（右侧面板）：**
  - **订阅管理：**
    - **订阅链接：** 在此处输入您的服务器订阅链接。
    - **组名称（可选）：** 输入新服务器组的名称。
    - **更新按钮：** 用于从订阅链接更新服务器列表。
  - **组操作：**
    - **Ping 组：** 对当前组中的所有服务器执行 TCP ping 测试。
    - **URL 测试组：** 对当前组中的所有服务器执行 URL 测试（这可能很耗时）。
    - **按 Ping 排序：** 按 ping 延迟对服务器进行排序。
    - **URL 测试（活动）：：** 对当前活动连接执行 URL 测试。
  - **手动添加：**
    - **添加单个服务器：** 通过粘贴其链接手动添加服务器。
  - **日志文本框：** 显示与应用程序活动相关的消息。

### 设置选项卡

此选项卡用于配置应用程序设置。

- **外观设置：**
  - **外观模式：** 更改显示模式（浅色、深色、系统）。
  - **颜色主题：** 更改应用程序的颜色主题（需要重新启动应用程序才能完全生效）。
- **网络设置：**
  - **连接模式：** 设置连接模式（基于规则或全局）。
  - **DNS 服务器：** 输入自定义 DNS 服务器（逗号分隔）。
  - **绕过域名：** 输入应绕过代理的域名（逗号分隔）。
  - **绕过 IP：** 输入应绕过代理的 IP 地址（逗号分隔）。

### 路由选项卡

该选项卡允许您定义自定义规则来控制网络流量的路由。您可以指定哪些流量直接连接到互联网，哪些通过代理，哪些被阻止。

- **规则列表：** 显示您已添加的所有自定义路由规则。
- **添加规则：** 打开一个对话框来创建新规则。
  - **规则类型：** 从 `domain`、`ip`、`process`、`geosite` 或 `geoip` 中选择。
  - **值:** 要匹配的值（例如 `google.com`、`1.1.1.1`、`iran`）。
  - **操作：** 选择是将匹配的流量 `direct`（直连）、`proxy`（代理）还是 `block`（阻止）。
- **编辑/删除规则：** 修改或删除现有规则。
- **保存/加载规则：** 将当前规则保存到设置文件或重新加载它们。

## 🤝 贡献

我们欢迎您的贡献！请阅读我们的 **贡献指南** 以开始。

## 📄 许可证

本项目根据 MIT 许可证获得许可。有关更多详细信息，请参阅 `LICENSE` 文件。
