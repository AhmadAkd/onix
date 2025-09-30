# Build Instructions

This document explains how to build Onix for different platforms.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## New Features in v1.1.0

- Enhanced Settings UI with Security, Performance, and Privacy tabs
- Real-time Speed Test functionality
- Auto-failover and improved Health Check
- Settings Search and Presets
- Advanced Security features (Kill Switch, DNS Leak Protection)
- Real-time Statistics and Monitoring
- Custom Themes and improved RTL support
- Comprehensive Privacy Controls
- Performance Analytics and Diagnostics
- Browser Integration and Keyboard Shortcuts
- Multi-user Support and Auto-backup

### Platform-specific requirements

#### Windows

- Visual Studio Build Tools (for some dependencies)
- Windows 10/11

#### macOS

- Xcode Command Line Tools
- macOS 10.15 or higher

#### Linux

- Build essentials (gcc, make, etc.)
- libffi-dev, libssl-dev

## Quick Build

### Universal Build Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/AhmadAkd/onix-client.git
cd onix-client

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build for current platform
python build_all.py
```

### Manual Build

#### Windows

```cmd
# Using batch script
build.bat

# Or using Python
python build_all.py
```

#### macOS/Linux

```bash
# Using shell script
chmod +x build.sh
./build.sh

# Or using Python
python build_all.py
```

## Build Output

The build process creates:

- **Executable**: `dist/onix` (or `dist/onix.exe` on Windows)
- **Package**: `dist/onix-v1.0.0-{platform}-{arch}.zip`

## Platform Support

| Platform | Architecture | Status |
|----------|-------------|---------|
| Windows | x64 | ✅ Supported |
| macOS | x64 (Intel) | ✅ Supported |
| macOS | ARM64 (Apple Silicon) | ✅ Supported |
| Linux | x64 | ✅ Supported |
| Linux | ARM64 | ✅ Supported |

## GitHub Actions

The project includes GitHub Actions workflows that automatically build for all platforms when a tag is pushed:

```bash
# Create and push a tag to trigger builds
git tag v1.0.0
git push origin v1.0.0
```

This will:

1. Build for Windows, macOS, and Linux
2. Create a GitHub release
3. Upload all platform packages

## Troubleshooting

### Common Issues

1. **PyInstaller not found**

   ```bash
   pip install pyinstaller
   ```

2. **Missing dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Permission denied (Linux/macOS)**

   ```bash
   chmod +x build.sh
   ```

4. **Core download fails**
   - Check internet connection
   - Verify GitHub API access
   - Try manual download

### Platform-specific Issues

#### Windows

- Ensure Visual Studio Build Tools are installed
- Run as Administrator if needed

#### macOS

- Install Xcode Command Line Tools: `xcode-select --install`
- May need to allow unsigned executables

#### Linux

- Install build essentials: `sudo apt-get install build-essential`
- Install additional dependencies: `sudo apt-get install libffi-dev libssl-dev`

## Development Build

For development, you can run the application directly without building:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Release Process

1. Update version numbers in relevant files
2. Update CHANGELOG.md
3. Create and push a tag:

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. GitHub Actions will automatically build and create a release

## File Structure

```
onix-client/
├── build_all.py          # Universal build script
├── build.bat            # Windows build script
├── build.sh             # Unix build script
├── .github/workflows/   # GitHub Actions
├── dist/                # Build output
├── assets/              # Icons and resources
├── translations/        # Translation files
└── ...
```
