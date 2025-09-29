# Multi-Platform Build Guide

This guide explains how to build Onix for Windows, macOS, and Linux.

## 🚀 Quick Start

### Method 1: GitHub Actions (Recommended)
```bash
# Create and push a tag to trigger automated builds
git tag v1.0.3
git push origin v1.0.3
```

This will automatically:
- Build for Windows, macOS, and Linux
- Create a GitHub release
- Upload all platform packages

### Method 2: Local Build
```bash
# Build for current platform
python build_all.py

# Cross-platform build (requires Docker)
python build_cross_platform.py
```

## 📋 Platform Support

| Platform | Architecture | Build Method | Status |
|----------|-------------|--------------|---------|
| **Windows** | x64 | Native | ✅ Tested |
| **macOS** | Intel | GitHub Actions | ✅ Ready |
| **macOS** | Apple Silicon | GitHub Actions | ✅ Ready |
| **Linux** | x64 | GitHub Actions | ✅ Ready |
| **Linux** | ARM64 | GitHub Actions | ✅ Ready |

## 🛠️ Build Methods

### 1. GitHub Actions (Automated)

**Advantages:**
- ✅ No local setup required
- ✅ Builds for all platforms automatically
- ✅ Creates releases automatically
- ✅ Uses clean environments

**Steps:**
1. Push code to GitHub
2. Create a tag: `git tag v1.0.3 && git push origin v1.0.3`
3. Wait for builds to complete
4. Download from GitHub releases

### 2. Local Native Build

**For Windows:**
```cmd
# Using batch script
build.bat

# Using Python script
python build_all.py
```

**For macOS:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build
python build_all.py
```

**For Linux:**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install build-essential libffi-dev libssl-dev

# Install Python dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build
python build_all.py
```

### 3. Cross-Platform Build (Docker)

**Requirements:**
- Docker Desktop installed
- Windows host system

**Steps:**
```bash
# Build for Linux from Windows
python build_cross_platform.py
```

## 📦 Build Output

Each build creates:

```
dist/
├── onix-v1.0.0-windows-amd64.zip    # Windows package
├── onix-v1.0.0-darwin-amd64.zip     # macOS Intel
├── onix-v1.0.0-darwin-arm64.zip     # macOS Apple Silicon
├── onix-v1.0.0-linux-amd64.zip      # Linux x64
└── onix-v1.0.0-linux-arm64.zip      # Linux ARM64
```

Each package contains:
- `onix` (or `onix.exe` on Windows) - Main executable
- `README.md` - Documentation
- `LICENSE` - License file
- `CHANGELOG.md` - Release notes

## 🔧 Troubleshooting

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

4. **Docker not found**
   - Install Docker Desktop
   - Ensure Docker is running

### Platform-specific Issues

#### Windows
- **Visual Studio Build Tools**: Install if missing
- **Antivirus**: May block PyInstaller output
- **Long paths**: Enable long path support

#### macOS
- **Xcode Command Line Tools**: `xcode-select --install`
- **Code signing**: May need to allow unsigned executables
- **Gatekeeper**: May block unsigned apps

#### Linux
- **Build essentials**: `sudo apt-get install build-essential`
- **Additional libraries**: `sudo apt-get install libffi-dev libssl-dev`
- **Permissions**: Ensure executable permissions

## 📊 Build Status

### Current Status
- ✅ **Windows x64**: Built and tested locally
- ⏳ **macOS Intel**: Ready for GitHub Actions
- ⏳ **macOS ARM64**: Ready for GitHub Actions
- ⏳ **Linux x64**: Ready for GitHub Actions
- ⏳ **Linux ARM64**: Ready for GitHub Actions

### GitHub Actions Status
Check build status at: `https://github.com/AhmadAkd/onix-client/actions`

## 🚀 Release Process

### Automated Release
1. Update version in code
2. Update CHANGELOG.md
3. Create and push tag:
   ```bash
   git tag v1.0.3
   git push origin v1.0.3
   ```
4. GitHub Actions builds and creates release
5. Download from GitHub releases page

### Manual Release
1. Build locally for each platform
2. Create GitHub release manually
3. Upload built packages

## 📁 File Structure

```
onix-client/
├── build_all.py              # Universal build script
├── build_cross_platform.py   # Cross-platform build script
├── build.bat                 # Windows build script
├── build.sh                  # Unix build script
├── .github/workflows/        # GitHub Actions
│   ├── build-all-platforms.yml
│   └── cross-platform-build.yml
├── dist/                     # Build output
├── assets/                   # Icons and resources
├── translations/             # Translation files
└── ...
```

## 🎯 Next Steps

1. **Test GitHub Actions**: Push a tag to trigger builds
2. **Verify builds**: Download and test on each platform
3. **Create release**: Use GitHub releases page
4. **Distribute**: Share download links with users

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Test locally first
4. Check system requirements

---

**Happy Building! 🎉**
