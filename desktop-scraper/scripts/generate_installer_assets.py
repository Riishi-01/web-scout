#!/usr/bin/env python3
"""
Installer Assets Generation Script for Local Web Scraper
=======================================================

This script generates professional installer assets including DMG backgrounds,
Windows installer graphics, and Linux desktop integration files.

Author: Claude Code Assistant
Date: December 13, 2024
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import subprocess

# Check for PIL availability
try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL.ImageColor import getrgb
except ImportError:
    print("❌ Pillow (PIL) not installed. Please install it:")
    print("pip install Pillow")
    sys.exit(1)

class InstallerAssetGenerator:
    """Generates professional installer assets for all platforms"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.assets_dir = self.base_dir / 'assets'
        self.installer_assets_dir = self.assets_dir / 'installer'
        
        # Create directories
        self.installer_assets_dir.mkdir(exist_ok=True)
        
        # Color scheme matching the app
        self.colors = {
            'primary': '#3b82f6',      # Blue-500
            'primary_dark': '#2563eb', # Blue-600
            'primary_darker': '#1d4ed8', # Blue-700
            'accent': '#10b981',       # Emerald-500
            'background': '#ffffff',   # White
            'dark': '#1f2937',         # Gray-800
            'gray': '#6b7280',         # Gray-500
            'light_gray': '#f3f4f6'    # Gray-100
        }
    
    def create_dmg_background(self, width: int = 660, height: int = 400) -> Image.Image:
        """Create macOS DMG background image"""
        print("🍎 Creating macOS DMG background...")
        
        # Create gradient background
        img = Image.new('RGB', (width, height), getrgb(self.colors['background']))
        draw = ImageDraw.Draw(img)
        
        # Create subtle gradient
        for y in range(height):
            alpha = int(255 * (1 - (y / height) * 0.1))
            color = (*getrgb(self.colors['light_gray']), alpha)
            draw.line([(0, y), (width, y)], fill=color[:3])
        
        # Add decorative elements
        self._add_spider_web_pattern(draw, width, height, alpha=30)
        
        # Add instruction text
        try:
            # Try to use system font
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Main instruction
        instruction_text = "Drag Local Web Scraper to Applications"
        text_bbox = draw.textbbox((0, 0), instruction_text, font=font_large)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2
        text_y = height - 80
        
        # Text shadow
        draw.text((text_x + 1, text_y + 1), instruction_text, 
                 fill=getrgb(self.colors['gray']), font=font_large)
        # Main text
        draw.text((text_x, text_y), instruction_text, 
                 fill=getrgb(self.colors['dark']), font=font_large)
        
        # Secondary instruction
        sub_text = "AI-powered web scraping made simple"
        sub_bbox = draw.textbbox((0, 0), sub_text, font=font_medium)
        sub_width = sub_bbox[2] - sub_bbox[0]
        sub_x = (width - sub_width) // 2
        sub_y = text_y + 35
        
        draw.text((sub_x, sub_y), sub_text, 
                 fill=getrgb(self.colors['gray']), font=font_medium)
        
        return img
    
    def create_windows_installer_header(self, width: int = 497, height: int = 55) -> Image.Image:
        """Create Windows installer header bitmap"""
        print("🪟 Creating Windows installer header...")
        
        # Create gradient background
        img = Image.new('RGB', (width, height), getrgb(self.colors['primary']))
        draw = ImageDraw.Draw(img)
        
        # Gradient effect
        for x in range(width):
            gradient_factor = x / width
            r, g, b = getrgb(self.colors['primary'])
            darker_r = int(r * (0.7 + gradient_factor * 0.3))
            darker_g = int(g * (0.7 + gradient_factor * 0.3))
            darker_b = int(b * (0.7 + gradient_factor * 0.3))
            
            draw.line([(x, 0), (x, height)], fill=(darker_r, darker_g, darker_b))
        
        # Add spider web pattern
        self._add_spider_web_pattern(draw, width, height, alpha=40, scale=0.3)
        
        # Add title text
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except:
            font = ImageFont.load_default()
        
        title = "Local Web Scraper"
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_height = text_bbox[3] - text_bbox[1]
        text_y = (height - text_height) // 2
        
        # Text shadow
        draw.text((21, text_y + 1), title, fill=(0, 0, 0, 100), font=font)
        # Main text
        draw.text((20, text_y), title, fill=getrgb(self.colors['background']), font=font)
        
        return img
    
    def create_windows_installer_sidebar(self, width: int = 164, height: int = 314) -> Image.Image:
        """Create Windows installer sidebar image"""
        print("🪟 Creating Windows installer sidebar...")
        
        # Create gradient background
        img = Image.new('RGB', (width, height), getrgb(self.colors['primary_dark']))
        draw = ImageDraw.Draw(img)
        
        # Vertical gradient
        for y in range(height):
            gradient_factor = y / height
            r, g, b = getrgb(self.colors['primary_dark'])
            lighter_r = int(r + (255 - r) * gradient_factor * 0.1)
            lighter_g = int(g + (255 - g) * gradient_factor * 0.1)
            lighter_b = int(b + (255 - b) * gradient_factor * 0.1)
            
            draw.line([(0, y), (width, y)], fill=(lighter_r, lighter_g, lighter_b))
        
        # Add decorative pattern
        self._add_spider_web_pattern(draw, width, height, alpha=20, scale=0.5)
        
        # Add app logo area (simplified icon)
        logo_size = 48
        logo_x = (width - logo_size) // 2
        logo_y = 40
        
        # Logo background circle
        logo_bbox = [
            logo_x, logo_y,
            logo_x + logo_size, logo_y + logo_size
        ]
        draw.ellipse(logo_bbox, fill=getrgb(self.colors['accent']))
        
        # Simple spider web in logo
        center_x = logo_x + logo_size // 2
        center_y = logo_y + logo_size // 2
        web_radius = logo_size // 3
        
        # Web lines
        for angle in range(0, 360, 60):
            import math
            end_x = center_x + web_radius * math.cos(math.radians(angle))
            end_y = center_y + web_radius * math.sin(math.radians(angle))
            draw.line([(center_x, center_y), (end_x, end_y)], 
                     fill=getrgb(self.colors['background']), width=2)
        
        # Add version info at bottom
        try:
            font_small = ImageFont.truetype("arial.ttf", 10)
        except:
            font_small = ImageFont.load_default()
        
        version_text = "v1.0.0"
        version_bbox = draw.textbbox((0, 0), version_text, font=font_small)
        version_width = version_bbox[2] - version_bbox[0]
        version_x = (width - version_width) // 2
        version_y = height - 30
        
        draw.text((version_x, version_y), version_text, 
                 fill=getrgb(self.colors['background']), font=font_small)
        
        return img
    
    def _add_spider_web_pattern(self, draw, width: int, height: int, alpha: int = 30, scale: float = 1.0):
        """Add subtle spider web pattern to image"""
        import math
        
        # Scale pattern
        web_size = int(100 * scale)
        spacing = int(120 * scale)
        
        # Create web pattern across the image
        for start_x in range(-web_size, width + web_size, spacing):
            for start_y in range(-web_size, height + web_size, spacing):
                center_x = start_x + web_size // 2
                center_y = start_y + web_size // 2
                
                # Skip if center is outside image
                if center_x < -50 or center_x > width + 50 or center_y < -50 or center_y > height + 50:
                    continue
                
                # Draw radial lines
                for angle in range(0, 360, 45):
                    end_x = center_x + (web_size // 2) * math.cos(math.radians(angle))
                    end_y = center_y + (web_size // 2) * math.sin(math.radians(angle))
                    
                    if 0 <= end_x <= width and 0 <= end_y <= height:
                        draw.line([(center_x, center_y), (end_x, end_y)], 
                                fill=(*getrgb(self.colors['primary']), alpha)[:3], width=1)
                
                # Draw concentric circles
                for radius in [web_size // 6, web_size // 4, web_size // 3]:
                    circle_bbox = [
                        center_x - radius, center_y - radius,
                        center_x + radius, center_y + radius
                    ]
                    
                    # Only draw if at least part of circle is visible
                    if (circle_bbox[2] >= 0 and circle_bbox[0] <= width and 
                        circle_bbox[3] >= 0 and circle_bbox[1] <= height):
                        draw.ellipse(circle_bbox, outline=(*getrgb(self.colors['primary']), alpha)[:3], width=1)
    
    def create_linux_desktop_file(self) -> str:
        """Create Linux .desktop file content"""
        print("🐧 Creating Linux desktop integration file...")
        
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Local Web Scraper
Comment=AI-powered web scraping application
Exec=local-web-scraper %U
Icon=local-web-scraper
StartupNotify=true
NoDisplay=false
Categories=Development;WebDevelopment;
Keywords=scraping;web;data;ai;automation;
MimeType=application/x-web-scraper-config;
Actions=NewWindow;

[Desktop Action NewWindow]
Name=New Window
Exec=local-web-scraper --new-window
Icon=local-web-scraper
"""
        return desktop_content
    
    def generate_all_assets(self):
        """Generate all installer assets"""
        print("🎨 Generating installer assets for Local Web Scraper...")
        print("=" * 60)
        
        generated_files = []
        
        # macOS DMG background
        dmg_bg = self.create_dmg_background()
        dmg_bg_path = self.installer_assets_dir / 'dmg-background.png'
        dmg_bg.save(dmg_bg_path, 'PNG')
        generated_files.append(dmg_bg_path)
        print(f"  ✅ DMG background: {dmg_bg_path.relative_to(self.base_dir)}")
        
        # DMG background @2x for Retina
        dmg_bg_2x = self.create_dmg_background(1320, 800)
        dmg_bg_2x_path = self.installer_assets_dir / 'dmg-background@2x.png'
        dmg_bg_2x.save(dmg_bg_2x_path, 'PNG')
        generated_files.append(dmg_bg_2x_path)
        print(f"  ✅ DMG background @2x: {dmg_bg_2x_path.relative_to(self.base_dir)}")
        
        # Windows installer header
        win_header = self.create_windows_installer_header()
        win_header_path = self.installer_assets_dir / 'installer-header.bmp'
        win_header.save(win_header_path, 'BMP')
        generated_files.append(win_header_path)
        print(f"  ✅ Windows header: {win_header_path.relative_to(self.base_dir)}")
        
        # Windows installer sidebar
        win_sidebar = self.create_windows_installer_sidebar()
        win_sidebar_path = self.installer_assets_dir / 'installer-sidebar.bmp'
        win_sidebar.save(win_sidebar_path, 'BMP')
        generated_files.append(win_sidebar_path)
        print(f"  ✅ Windows sidebar: {win_sidebar_path.relative_to(self.base_dir)}")
        
        # Linux desktop file
        desktop_content = self.create_linux_desktop_file()
        desktop_file_path = self.installer_assets_dir / 'local-web-scraper.desktop'
        with open(desktop_file_path, 'w') as f:
            f.write(desktop_content)
        generated_files.append(desktop_file_path)
        print(f"  ✅ Linux desktop file: {desktop_file_path.relative_to(self.base_dir)}")
        
        # Copy existing icons for installer use
        self._copy_installer_icons()
        
        print("\n" + "=" * 60)
        print(f"🎉 Generated {len(generated_files)} installer assets")
        
        return generated_files
    
    def _copy_installer_icons(self):
        """Copy and prepare icons for installer use"""
        print("📋 Preparing installer icons...")
        
        # Copy main icons to installer directory for easier reference
        icon_mappings = {
            'icon.ico': 'installer-icon.ico',
            'icon.icns': 'installer-icon.icns', 
            'icon.png': 'installer-icon.png'
        }
        
        for source, target in icon_mappings.items():
            source_path = self.assets_dir / source
            target_path = self.installer_assets_dir / target
            
            if source_path.exists():
                target_path.write_bytes(source_path.read_bytes())
                print(f"  ✅ Copied {source} → {target}")
    
    def update_package_json(self):
        """Update package.json with enhanced installer configuration"""
        print("📝 Updating package.json with installer enhancements...")
        
        package_path = self.base_dir / 'package.json'
        
        # Check if jq is available
        try:
            subprocess.run(['which', 'jq'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("  ⚠️  jq not found - manual package.json update required")
            self._show_manual_package_config()
            return
        
        # Backup original
        backup_path = package_path.with_suffix('.json.backup-installer')
        backup_path.write_bytes(package_path.read_bytes())
        
        try:
            # macOS DMG configuration
            dmg_config = {
                "background": "assets/installer/dmg-background.png",
                "iconSize": 100,
                "iconTextSize": 12,
                "window": {
                    "width": 660,
                    "height": 400
                },
                "contents": [
                    {"x": 180, "y": 170, "type": "file"},
                    {"x": 480, "y": 170, "type": "link", "path": "/Applications"}
                ]
            }
            
            # Windows NSIS configuration
            nsis_config = {
                "oneClick": False,
                "allowToChangeInstallationDirectory": True,
                "allowElevation": True,
                "installerIcon": "assets/installer/installer-icon.ico",
                "uninstallerIcon": "assets/installer/installer-icon.ico",
                "installerHeader": "assets/installer/installer-header.bmp",
                "installerSidebar": "assets/installer/installer-sidebar.bmp",
                "createDesktopShortcut": "always",
                "createStartMenuShortcut": True,
                "shortcutName": "Local Web Scraper",
                "displayLanguageSelector": True
            }
            
            # Linux configuration
            linux_desktop = {
                "Name": "Local Web Scraper",
                "Comment": "AI-powered web scraping application",
                "Categories": "Development;WebDevelopment;",
                "Keywords": "scraping;web;data;ai;automation;"
            }
            
            # Update package.json using jq
            import json
            import tempfile
            
            # Read current package.json
            with open(package_path, 'r') as f:
                package_data = json.load(f)
            
            # Update build configuration
            if 'build' not in package_data:
                package_data['build'] = {}
            
            if 'mac' not in package_data['build']:
                package_data['build']['mac'] = {}
            package_data['build']['mac']['dmg'] = dmg_config
            
            if 'win' not in package_data['build']:
                package_data['build']['win'] = {}
            package_data['build']['win']['nsis'] = nsis_config
            
            if 'linux' not in package_data['build']:
                package_data['build']['linux'] = {}
            package_data['build']['linux']['desktop'] = linux_desktop
            
            # Add additional Linux targets
            package_data['build']['linux']['target'] = [
                {"target": "AppImage", "arch": ["x64"]},
                {"target": "deb", "arch": ["x64"]},
                {"target": "rpm", "arch": ["x64"]}
            ]
            
            # Write updated package.json
            with open(package_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            print(f"  ✅ Updated package.json")
            print(f"  📋 Backup saved: {backup_path.relative_to(self.base_dir)}")
            
        except Exception as e:
            print(f"  ❌ Failed to update package.json: {e}")
            # Restore backup
            package_path.write_bytes(backup_path.read_bytes())
            self._show_manual_package_config()
    
    def _show_manual_package_config(self):
        """Show manual package.json configuration"""
        print("\n📋 Manual package.json configuration needed:")
        print("Add the following to your build configuration:")
        
        config_text = '''
{
  "build": {
    "mac": {
      "dmg": {
        "background": "assets/installer/dmg-background.png",
        "iconSize": 100,
        "iconTextSize": 12,
        "window": {
          "width": 660,
          "height": 400
        },
        "contents": [
          {"x": 180, "y": 170, "type": "file"},
          {"x": 480, "y": 170, "type": "link", "path": "/Applications"}
        ]
      }
    },
    "win": {
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
        "shortcutName": "Local Web Scraper"
      }
    },
    "linux": {
      "target": [
        {"target": "AppImage", "arch": ["x64"]},
        {"target": "deb", "arch": ["x64"]},
        {"target": "rpm", "arch": ["x64"]}
      ],
      "desktop": {
        "Name": "Local Web Scraper",
        "Comment": "AI-powered web scraping application",
        "Categories": "Development;WebDevelopment;",
        "Keywords": "scraping;web;data;ai;automation;"
      }
    }
  }
}
'''
        print(config_text)


def main():
    """Main function to generate installer assets"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate installer assets for Local Web Scraper")
    parser.add_argument("--base-dir", type=str, 
                       default="/Users/rr/MLOPS/Crawler_max/desktop-scraper",
                       help="Base directory of the desktop app")
    parser.add_argument("--update-package", action="store_true",
                       help="Update package.json with installer configuration")
    
    args = parser.parse_args()
    
    # Verify base directory exists
    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f"❌ Base directory not found: {base_dir}")
        sys.exit(1)
    
    # Generate assets
    generator = InstallerAssetGenerator(str(base_dir))
    generated_files = generator.generate_all_assets()
    
    # Update package.json if requested
    if args.update_package:
        generator.update_package_json()
    
    print(f"\n✨ Installer assets generation completed!")
    print("🔧 Next steps:")
    print("  1. Review generated assets in assets/installer/")
    print("  2. Build application: npm run build:electron")
    print("  3. Test installers on each platform")
    print("  4. Configure code signing for production")


if __name__ == "__main__":
    main()