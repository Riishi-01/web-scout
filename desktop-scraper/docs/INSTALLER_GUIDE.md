# Professional Installer Guide for Local Web Scraper

This guide covers the complete installer setup and distribution strategy for the Local Web Scraper desktop application.

## 🎯 Overview

The Local Web Scraper now includes professional-grade installers for all platforms with:
- **Custom Branding**: Professional visual design with application branding
- **Enhanced User Experience**: Platform-specific installation workflows
- **Multiple Package Formats**: DMG, NSIS, AppImage, DEB, and RPM support
- **Auto-Update Ready**: Built-in update mechanism support

## 📦 Current Installer Status

### ✅ Successfully Generated Installers

| Platform | Format | File Size | Status |
|----------|--------|-----------|--------|
| **macOS (Intel)** | DMG | ~140MB | ✅ Ready |
| **macOS (Apple Silicon)** | DMG | ~138MB | ✅ Ready |
| **Windows** | NSIS Installer | ~142MB | ✅ Ready |
| **Linux** | AppImage | ~148MB | ✅ Ready |

### 🎨 Professional Installer Assets

#### macOS DMG
- **Custom Background**: Professional spider web + AI theme design
- **Drag-to-Applications Layout**: Intuitive installation workflow
- **Retina Support**: High-resolution background for Retina displays
- **Branded Window**: Custom DMG window size and positioning

#### Windows NSIS
- **Custom Graphics**: Professional header and sidebar images
- **Multi-Language Support**: 26+ languages supported
- **Installation Options**: 
  - Custom installation directory selection
  - Desktop shortcut creation
  - Start Menu integration
  - Uninstaller included

#### Linux AppImage
- **Desktop Integration**: `.desktop` file for system integration
- **File Associations**: Web scraper configuration file support
- **System Menu**: Proper categorization (Development > WebDevelopment)
- **Keywords**: SEO-optimized for application discovery

## 🔧 Technical Configuration

### Package.json Build Configuration

```json
{
  "build": {
    "mac": {
      "target": [
        { "target": "dmg", "arch": ["x64", "arm64"] }
      ],
      "hardenedRuntime": true,
      "gatekeeperAssess": false
    },
    "win": {
      "target": [
        { "target": "nsis", "arch": ["x64"] }
      ],
      "signingHashAlgorithms": ["sha256"],
      "signDlls": true
    },
    "linux": {
      "target": [
        { "target": "AppImage", "arch": ["x64"] },
        { "target": "deb", "arch": ["x64"] },
        { "target": "rpm", "arch": ["x64"] }
      ],
      "desktop": {
        "Name": "Local Web Scraper",
        "Comment": "AI-powered web scraping application",
        "Categories": "Development;WebDevelopment;",
        "Keywords": "scraping;web;data;ai;automation;"
      }
    },
    "dmg": {
      "background": "assets/installer/dmg-background.png",
      "iconSize": 100,
      "iconTextSize": 12,
      "window": { "width": 660, "height": 400 },
      "contents": [
        { "x": 180, "y": 170, "type": "file" },
        { "x": 480, "y": 170, "type": "link", "path": "/Applications" }
      ]
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "allowElevation": true,
      "installerIcon": "assets/installer/installer-icon.ico",
      "uninstallerIcon": "assets/installer/installer-icon.ico",
      "installerHeader": "assets/installer/installer-header.bmp",
      "installerSidebar": "assets/installer/installer-sidebar.bmp",
      "createDesktopShortcut": "always",
      "createStartMenuShortcut": true,
      "shortcutName": "Local Web Scraper",
      "displayLanguageSelector": true
    }
  }
}
```

### Generated Installer Assets

```
assets/installer/
├── dmg-background.png          # macOS DMG background (660x400)
├── dmg-background@2x.png       # Retina DMG background (1320x800)
├── installer-header.bmp        # Windows installer header (497x55)
├── installer-sidebar.bmp       # Windows installer sidebar (164x314)
├── installer-icon.ico          # Windows installer icon
├── installer-icon.icns         # macOS installer icon
├── installer-icon.png          # Linux installer icon
└── local-web-scraper.desktop   # Linux desktop integration
```

## 🚀 Building Installers

### Standard Build
```bash
npm run build:electron
```

### Platform-Specific Builds
```bash
# macOS only
npm run build:mac

# Windows only (requires Windows or cross-compilation)
npm run build:win

# Linux only
npm run build:linux
```

### Signed Build (Production)
```bash
# Configure signing environment
cp .env.signing.template .env.signing
# Edit .env.signing with your certificates

# Build with signing
./scripts/build_signed.sh
```

## 🔐 Code Signing Status

### Current Status (Development)
- **macOS**: Unsigned (will show security warnings)
- **Windows**: Unsigned (will trigger SmartScreen warnings)
- **Linux**: No signing required for AppImage

### Production Requirements
- **macOS**: Apple Developer ID Application certificate ($99/year)
- **Windows**: Code Signing certificate ($200-600/year)
- **Linux**: Optional GPG signing for package integrity

### Setup Code Signing
```bash
# Run setup script
./scripts/setup_code_signing.sh

# Check current status
./scripts/setup_code_signing.sh --check

# View instructions
./scripts/setup_code_signing.sh --instructions
```

## 📱 Platform-Specific Installation

### macOS Installation
1. **Download**: `Local Web Scraper-1.0.0.dmg` (Intel) or `Local Web Scraper-1.0.0-arm64.dmg` (Apple Silicon)
2. **Mount**: Double-click DMG file to mount
3. **Install**: Drag "Local Web Scraper" to Applications folder
4. **Launch**: Open from Applications folder
5. **Security**: May require "Open Anyway" in Security & Privacy settings (unsigned builds)

**File Size**: ~140MB | **macOS Version**: 10.12+ (Sierra)

### Windows Installation
1. **Download**: `Local Web Scraper Setup 1.0.0.exe`
2. **Run**: Double-click installer executable
3. **Security**: Click "More info" → "Run anyway" if SmartScreen appears (unsigned builds)
4. **Install**: Follow installation wizard
   - Choose installation directory
   - Select desktop shortcut option
   - Choose Start Menu folder
5. **Launch**: Use desktop shortcut or Start Menu

**File Size**: ~142MB | **Windows Version**: Windows 10+ (x64)

### Linux Installation

#### AppImage (Recommended)
```bash
# Download
wget https://github.com/your-repo/releases/download/v1.0.0/Local-Web-Scraper-1.0.0.AppImage

# Make executable
chmod +x Local-Web-Scraper-1.0.0.AppImage

# Run
./Local-Web-Scraper-1.0.0.AppImage
```

#### DEB Package (Ubuntu/Debian)
```bash
# Download and install
wget https://github.com/your-repo/releases/download/v1.0.0/local-web-scraper_1.0.0_amd64.deb
sudo dpkg -i local-web-scraper_1.0.0_amd64.deb

# Fix dependencies if needed
sudo apt-get install -f
```

#### RPM Package (Red Hat/Fedora/CentOS)
```bash
# Download and install
wget https://github.com/your-repo/releases/download/v1.0.0/local-web-scraper-1.0.0.x86_64.rpm
sudo rpm -i local-web-scraper-1.0.0.x86_64.rpm
```

**File Size**: ~148MB | **Linux**: x64 architecture required

## 🔄 Auto-Update System

### Current Configuration
- **Electron-Updater**: Integrated and configured
- **Update Server**: Ready for GitHub Releases integration
- **Blockmap Files**: Generated for efficient delta updates
- **Platform Support**: All platforms supported

### Update Server Setup
```json
{
  "publish": {
    "provider": "github",
    "owner": "your-username",
    "repo": "desktop-scraper"
  }
}
```

### Update Process
1. **Check for Updates**: Automatic on app launch
2. **Download**: Background download of updates
3. **Install**: User-prompted installation
4. **Restart**: Automatic app restart with new version

## 📊 Distribution Strategy

### Download Hosting Options

#### GitHub Releases (Recommended - Free)
- **Pros**: Free, integrated with development workflow, reliable CDN
- **Cons**: 2GB file size limit, requires GitHub account for private repos
- **Setup**: Automated with GitHub Actions

#### Custom CDN
- **Pros**: Full control, custom domain, analytics
- **Cons**: Cost, maintenance overhead
- **Providers**: AWS CloudFront, Cloudflare, KeyCDN

### Release Automation

#### GitHub Actions Workflow
```yaml
name: Build and Release
on:
  push:
    tags: ['v*']
jobs:
  build:
    strategy:
      matrix:
        os: [macos-latest, windows-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Build and release
        env:
          CSC_LINK: ${{ secrets.CSC_LINK }}
          CSC_KEY_PASSWORD: ${{ secrets.CSC_KEY_PASSWORD }}
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_ID_PASSWORD: ${{ secrets.APPLE_ID_PASSWORD }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npm run dist
```

## 🎨 Customizing Installer Assets

### Regenerate Assets
```bash
# Regenerate all installer assets
python scripts/generate_installer_assets.py

# Update package.json configuration
python scripts/generate_installer_assets.py --update-package
```

### Asset Specifications

#### DMG Background
- **Size**: 660x400 (standard), 1320x800 (@2x)
- **Format**: PNG with transparency support
- **Design**: Professional branding with spider web + AI theme

#### Windows Installer Graphics
- **Header**: 497x55 pixels, BMP format
- **Sidebar**: 164x314 pixels, BMP format
- **Design**: Gradient backgrounds with branding elements

#### Linux Desktop Integration
- **Desktop File**: `.desktop` specification compliant
- **Categories**: Development;WebDevelopment;
- **Keywords**: Optimized for application discovery

## 🔍 Quality Assurance

### Pre-Release Testing Checklist

#### macOS Testing
- [ ] DMG mounts correctly
- [ ] Drag-to-Applications works
- [ ] App launches without crashes
- [ ] Custom background displays properly
- [ ] Gatekeeper warnings appropriate for signing status

#### Windows Testing
- [ ] Installer runs without errors
- [ ] Custom graphics display correctly
- [ ] Installation options work (directory, shortcuts)
- [ ] App launches from shortcuts
- [ ] Uninstaller removes all components
- [ ] SmartScreen warnings appropriate for signing status

#### Linux Testing
- [ ] AppImage is executable
- [ ] Desktop integration works
- [ ] File associations register correctly
- [ ] App appears in application menu
- [ ] All functionality works as expected

### Performance Validation
- **Startup Time**: < 5 seconds on modern hardware
- **Memory Usage**: < 500MB during normal operation
- **Install Size**: < 200MB for all platforms
- **Install Time**: < 2 minutes on modern systems

## 📈 Analytics and Monitoring

### Installation Metrics
- **Download Tracking**: GitHub Releases provides download statistics
- **Installation Success Rate**: Monitor through app telemetry
- **Platform Distribution**: Track platform preferences
- **Update Adoption**: Monitor auto-update success rates

### User Feedback
- **Installation Issues**: Monitor support channels for installer problems
- **Platform Requests**: Track requests for additional platforms/formats
- **Update Problems**: Monitor auto-update failure reports

## 🔒 Security Considerations

### Installer Security
- **Code Signing**: Essential for trusted distribution
- **Checksum Verification**: Provide SHA256 hashes for all downloads
- **Secure Distribution**: Use HTTPS for all download links
- **Integrity Checks**: Validate installer integrity before execution

### User Security
- **Clear Instructions**: Provide detailed installation instructions
- **Warning Management**: Explain security warnings for unsigned builds
- **Source Verification**: Direct users to official download sources only
- **Update Security**: Ensure auto-updates use secure channels

## 🚀 Future Enhancements

### Phase 1: Code Signing
- [ ] Obtain Apple Developer certificate
- [ ] Purchase Windows code signing certificate
- [ ] Implement signed builds
- [ ] Test signed installers

### Phase 2: Distribution Optimization
- [ ] Set up automated release pipeline
- [ ] Implement delta updates
- [ ] Add installer analytics
- [ ] Optimize download sizes

### Phase 3: Additional Platforms
- [ ] Windows ARM64 support
- [ ] Linux ARM64/ARM32 support
- [ ] Portable Windows version
- [ ] macOS App Store distribution

### Phase 4: Enterprise Features
- [ ] Silent installation options
- [ ] Group Policy templates
- [ ] Enterprise deployment guides
- [ ] Volume licensing options

## 📞 Support and Troubleshooting

### Common Installation Issues

#### macOS
- **"App can't be opened"**: Security & Privacy → Open Anyway
- **"Damaged application"**: Download fresh copy, verify signature
- **"App not found"**: Ensure drag-to-Applications completed

#### Windows
- **SmartScreen warning**: Click "More info" → "Run anyway"
- **Installation fails**: Run as Administrator
- **Antivirus blocks**: Whitelist installer and application

#### Linux
- **AppImage won't run**: `chmod +x` to make executable
- **Missing dependencies**: Install required system libraries
- **Desktop integration fails**: Manually copy .desktop file

### Getting Help
- **Documentation**: Check docs/ directory for detailed guides
- **Issues**: Report problems on GitHub Issues
- **Community**: Join community discussions
- **Support**: Contact support for critical issues

---

**Generated by Local Web Scraper installer system**  
**Last Updated**: December 13, 2024  
**Version**: 1.0.0