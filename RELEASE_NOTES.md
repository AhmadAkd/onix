# Release Notes

## v1.1.0 - 2025-09-30

### 🎉 Major Features

#### Enhanced Settings UI
- **New Security Tab**: Advanced security settings including Kill Switch, DNS Leak Protection, Certificate Pinning, and IPv6 Leak Protection
- **New Performance Tab**: Performance monitoring, connection multiplexing, bandwidth limiting, and statistics
- **New Privacy Tab**: Comprehensive privacy controls, data collection settings, and privacy actions
- **Settings Search**: Quick search functionality across all settings
- **Settings Presets**: Pre-configured settings (Balanced, Performance, Security, Privacy)

#### Real-time Speed Test
- Live speed testing with detailed analytics
- Real-time monitoring of connection performance
- Performance dashboard with visual metrics
- Speed test results integration with server management

#### Auto-failover
- Automatic server switching on connection failure
- Improved health checking with EMA smoothing
- Exponential backoff for failed connections
- Smart routing based on performance metrics

#### Advanced Security Features
- **Kill Switch**: Automatic connection protection on proxy failure
- **DNS Leak Protection**: Prevent DNS leaks and ensure privacy
- **Certificate Pinning**: Enhanced security for TLS connections
- **IPv6 Leak Protection**: Comprehensive IPv6 leak prevention

#### Privacy Controls
- Disable telemetry, crash reports, and usage statistics
- Clear logs on exit and disable detailed logging
- Disable DNS query logging and traffic statistics
- Export privacy settings and clear all data

#### Performance Analytics
- Real-time statistics collection
- Performance monitoring and diagnostics
- Connection analytics and insights
- Network diagnostics and troubleshooting

#### Custom Themes
- Enhanced theming system with RTL support
- Multiple theme options
- Custom theme management
- Improved UI responsiveness

#### Multi-user Support
- User management and profile system
- Auto-backup functionality
- Configuration templates
- User-specific settings

#### Browser Integration
- Seamless browser integration capabilities
- Keyboard shortcuts for quick access
- Enhanced system tray functionality
- System notifications for important events

### 🔧 Technical Improvements

#### New Service Modules
- `SpeedTestService`: Real-time speed testing
- `SecurityService`: Advanced security features
- `StatisticsService`: Real-time monitoring
- `NotificationService`: System notifications
- `BackupService`: Auto-backup functionality
- `DiagnosticsService`: Network diagnostics
- `IntegrationService`: Browser and keyboard integration
- `UserManagementService`: Multi-user support
- `CustomThemeManager`: Theme management

#### Enhanced Settings Management
- Comprehensive settings system
- Better organization and categorization
- Improved settings validation
- Enhanced error handling

#### Xray Integration
- Fixed configuration issues for URL testing
- Improved Xray/Sing-box integration
- Better error handling and diagnostics
- Enhanced stability and reliability

#### UI/UX Improvements
- Enhanced layout and styling
- Better responsiveness and performance
- Improved error handling and user feedback
- Enhanced RTL support

### 🐛 Bug Fixes

- Fixed Xray configuration issues causing test core failures
- Resolved UI layout problems in settings view
- Fixed selected tab text readability issues
- Improved error handling in core management
- Enhanced stability and reliability

### 📊 Statistics

- **30 files modified**
- **5,617 lines added**
- **312 lines removed**
- **10 new service modules created**
- **Enhanced UI components and styling**

### 🚀 Getting Started

1. Download the latest release from GitHub
2. Extract and run the application
3. Explore the new Settings tabs
4. Try the Speed Test functionality
5. Configure Auto-failover settings
6. Customize your theme and privacy settings

### 📝 Migration Notes

- Settings are automatically migrated from previous versions
- New features are enabled by default with safe defaults
- Privacy settings can be customized in the new Privacy tab
- Performance settings can be optimized in the new Performance tab

### 🔗 Links

- [GitHub Repository](https://github.com/AhmadAkd/onix-client)
- [Documentation](https://github.com/AhmadAkd/onix-client#readme)
- [Issues](https://github.com/AhmadAkd/onix-client/issues)
- [Releases](https://github.com/AhmadAkd/onix-client/releases)

---

## Previous Releases

### v1.0.0 - 2025-09-29
- Complete UI refactoring with modern PySide6 interface
- Multi-language support (Persian, Russian, Arabic, Chinese)
- Comprehensive server management system
- Health checking and ping services
- QR code generation for server configurations
- Advanced routing rules management
- Subscription management with auto-update
- System tray integration
- Modern icon set and UI components
- Comprehensive translation system
