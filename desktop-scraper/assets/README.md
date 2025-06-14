# Local Web Scraper - Application Icons

This directory contains the application icons for the Local Web Scraper desktop application.

## 🎨 Icon Design

The icon represents:
- **Web Scraping**: Spider web pattern indicating web data extraction
- **AI/Local Processing**: Central circuit-like pattern representing artificial intelligence
- **Professional Look**: Blue color scheme matching the application's branding
- **Cross-Platform**: Designed to work well at all sizes on Windows, macOS, and Linux

## 📁 Icon Files

### Platform-Specific Icons
- `icon.icns` - macOS application icon (multiple resolutions bundled)
- `icon.ico` - Windows application icon (multiple resolutions bundled)
- `icon.png` - Linux application icon (512x512 pixels)

### Individual PNG Files
- `icon_16x16.png` - Small system icon
- `icon_24x24.png` - Small Windows icon
- `icon_32x32.png` - Standard icon
- `icon_48x48.png` - Medium icon
- `icon_64x64.png` - Large icon
- `icon_128x128.png` - High DPI icon
- `icon_256x256.png` - Very high DPI icon
- `icon_512x512.png` - Linux app icon
- `icon_1024x1024.png` - macOS Retina icon

## 🔧 Usage

These icons are automatically used by Electron Builder when packaging the application:
- The build configuration in `package.json` references these files
- Icons are embedded into the final application packages
- Different platforms use their respective icon formats

## 🎯 Color Scheme

- **Primary Blue**: #3b82f6 (Blue-500)
- **Accent Green**: #10b981 (Emerald-500) 
- **Background**: White/Transparent
- **Web Pattern**: White overlay

## 🔄 Regeneration

To regenerate these icons, run:

```bash
python scripts/generate_icons.py
```

This script will recreate all icon files with the current design.

## 📋 Requirements Met

✅ **macOS**: ICNS format with multiple resolutions (16px to 1024px)
✅ **Windows**: ICO format with standard Windows sizes
✅ **Linux**: High-resolution PNG (512x512)
✅ **Electron**: All required formats for cross-platform distribution
✅ **Web**: Favicon and web app icons included

The icons follow platform-specific guidelines and provide a professional appearance across all operating systems.