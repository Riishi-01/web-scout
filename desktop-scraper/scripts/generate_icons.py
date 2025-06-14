#!/usr/bin/env python3
"""
Icon Generation Script for Local Web Scraper Desktop App
========================================================

This script generates all required application icons for the Local Web Scraper
desktop application, including platform-specific formats and sizes.

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

# Check for additional tools
IMAGEMAGICK_AVAILABLE = False
try:
    result = subprocess.run(['convert', '-version'], capture_output=True, text=True)
    if result.returncode == 0:
        IMAGEMAGICK_AVAILABLE = True
        print("✅ ImageMagick detected - will use for ICO/ICNS generation")
except FileNotFoundError:
    print("⚠️  ImageMagick not found - will create PNG files only")
    print("   Install ImageMagick for ICO/ICNS support:")
    print("   macOS: brew install imagemagick")
    print("   Ubuntu: sudo apt-get install imagemagick")

class IconDesigner:
    """Creates the Local Web Scraper application icon"""
    
    def __init__(self):
        # Color scheme based on app's primary colors
        self.colors = {
            'primary': '#3b82f6',      # Blue-500
            'primary_dark': '#2563eb', # Blue-600
            'primary_darker': '#1d4ed8', # Blue-700
            'accent': '#10b981',       # Emerald-500
            'background': '#ffffff',   # White
            'dark': '#1f2937',         # Gray-800
            'gray': '#6b7280'          # Gray-500
        }
    
    def create_base_icon(self, size: int) -> Image.Image:
        """Create the base icon design"""
        # Create canvas with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate proportional sizes
        margin = size * 0.1
        center = size // 2
        
        # Background circle (subtle)
        circle_radius = size * 0.45
        circle_bbox = [
            center - circle_radius,
            center - circle_radius,
            center + circle_radius,
            center + circle_radius
        ]
        
        # Draw background gradient effect (simulate with multiple circles)
        for i in range(5):
            alpha = 40 - (i * 8)
            radius_offset = i * 2
            circle_color = (*getrgb(self.colors['primary']), alpha)
            
            gradient_bbox = [
                circle_bbox[0] + radius_offset,
                circle_bbox[1] + radius_offset,
                circle_bbox[2] - radius_offset,
                circle_bbox[3] - radius_offset
            ]
            
            # Only draw if bbox is valid
            if gradient_bbox[2] > gradient_bbox[0] and gradient_bbox[3] > gradient_bbox[1]:
                draw.ellipse(gradient_bbox, fill=circle_color)
        
        # Main circle background
        main_circle_color = (*getrgb(self.colors['primary']), 200)
        draw.ellipse(circle_bbox, fill=main_circle_color)
        
        # Spider web design (representing web scraping)
        web_center_x, web_center_y = center, center
        web_radius = size * 0.35
        
        # Draw web lines
        web_color = (*getrgb(self.colors['background']), 255)
        line_width = max(1, size // 64)
        
        # Radial lines (8 directions)
        for angle in range(0, 360, 45):
            import math
            end_x = web_center_x + web_radius * math.cos(math.radians(angle))
            end_y = web_center_y + web_radius * math.sin(math.radians(angle))
            draw.line(
                [(web_center_x, web_center_y), (end_x, end_y)],
                fill=web_color,
                width=line_width
            )
        
        # Concentric circles for web
        for radius_multiplier in [0.15, 0.25, 0.35]:
            web_radius_current = size * radius_multiplier
            web_circle_bbox = [
                web_center_x - web_radius_current,
                web_center_y - web_radius_current,
                web_center_x + web_radius_current,
                web_center_y + web_radius_current
            ]
            draw.ellipse(web_circle_bbox, outline=web_color, width=line_width)
        
        # AI/Brain symbol in center
        brain_size = size * 0.12
        brain_x = center - brain_size // 2
        brain_y = center - brain_size // 2
        
        # Simple AI symbol (circuit-like pattern)
        ai_color = (*getrgb(self.colors['accent']), 255)
        
        # Central node
        node_radius = brain_size * 0.3
        node_bbox = [
            brain_x + brain_size//2 - node_radius,
            brain_y + brain_size//2 - node_radius,
            brain_x + brain_size//2 + node_radius,
            brain_y + brain_size//2 + node_radius
        ]
        draw.ellipse(node_bbox, fill=ai_color)
        
        # Connection nodes
        node_positions = [
            (brain_x, brain_y),
            (brain_x + brain_size, brain_y),
            (brain_x, brain_y + brain_size),
            (brain_x + brain_size, brain_y + brain_size)
        ]
        
        small_node_radius = node_radius * 0.4
        for pos_x, pos_y in node_positions:
            small_node_bbox = [
                pos_x - small_node_radius,
                pos_y - small_node_radius,
                pos_x + small_node_radius,
                pos_y + small_node_radius
            ]
            draw.ellipse(small_node_bbox, fill=ai_color)
            
            # Draw connection lines
            draw.line(
                [(brain_x + brain_size//2, brain_y + brain_size//2), (pos_x, pos_y)],
                fill=ai_color,
                width=max(1, line_width//2)
            )
        
        # Add data extraction arrows (small)
        arrow_color = (*getrgb(self.colors['background']), 200)
        arrow_size = size * 0.08
        
        # Right arrow
        arrow_x = center + size * 0.25
        arrow_y = center
        arrow_points = [
            (arrow_x, arrow_y - arrow_size//2),
            (arrow_x + arrow_size, arrow_y),
            (arrow_x, arrow_y + arrow_size//2),
            (arrow_x + arrow_size//3, arrow_y)
        ]
        draw.polygon(arrow_points, fill=arrow_color)
        
        return img
    
    def create_favicon(self, size: int = 32) -> Image.Image:
        """Create a simplified favicon version"""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        center = size // 2
        
        # Simple design for small size
        # Background circle
        circle_radius = size * 0.4
        circle_bbox = [
            center - circle_radius,
            center - circle_radius,
            center + circle_radius,
            center + circle_radius
        ]
        
        circle_color = getrgb(self.colors['primary'])
        draw.ellipse(circle_bbox, fill=circle_color)
        
        # Simple web pattern
        web_color = getrgb(self.colors['background'])
        line_width = max(1, size // 16)
        
        # Cross lines
        draw.line([(center, center - circle_radius), (center, center + circle_radius)], 
                 fill=web_color, width=line_width)
        draw.line([(center - circle_radius, center), (center + circle_radius, center)], 
                 fill=web_color, width=line_width)
        
        # Central dot
        dot_radius = size * 0.08
        dot_bbox = [
            center - dot_radius,
            center - dot_radius,
            center + dot_radius,
            center + dot_radius
        ]
        draw.ellipse(dot_bbox, fill=getrgb(self.colors['accent']))
        
        return img


class IconGenerator:
    """Generates all required icon formats and sizes"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.assets_dir = self.base_dir / 'assets'
        self.public_dir = self.base_dir / 'public'
        self.designer = IconDesigner()
        
        # Create directories if they don't exist
        self.assets_dir.mkdir(exist_ok=True)
        self.public_dir.mkdir(exist_ok=True)
    
    def generate_png_icons(self):
        """Generate PNG icons in various sizes"""
        print("🎨 Generating PNG icons...")
        
        # Standard sizes for different purposes
        sizes = {
            16: "Small system icon",
            24: "Small Windows icon",
            32: "Standard icon",
            48: "Medium icon",
            64: "Large icon",
            128: "High DPI icon",
            256: "Very high DPI icon",
            512: "Linux app icon",
            1024: "macOS Retina icon"
        }
        
        generated_files = []
        
        for size, description in sizes.items():
            print(f"  📏 Creating {size}x{size} icon ({description})")
            
            # Generate main icon
            icon = self.designer.create_base_icon(size)
            
            # Save main PNG
            png_path = self.assets_dir / f'icon_{size}x{size}.png'
            icon.save(png_path, 'PNG')
            generated_files.append(png_path)
            
            # Save the 512x512 as the main Linux icon
            if size == 512:
                main_png_path = self.assets_dir / 'icon.png'
                icon.save(main_png_path, 'PNG')
                generated_files.append(main_png_path)
                print(f"  ✅ Saved Linux icon: {main_png_path}")
        
        # Generate favicon
        print("  🌐 Creating favicon...")
        favicon = self.designer.create_favicon(32)
        favicon_path = self.public_dir / 'favicon.ico'
        
        # Save as PNG first, then convert to ICO if ImageMagick available
        favicon_png_path = self.public_dir / 'favicon.png'
        favicon.save(favicon_png_path, 'PNG')
        
        if IMAGEMAGICK_AVAILABLE:
            try:
                subprocess.run([
                    'convert', str(favicon_png_path), str(favicon_path)
                ], check=True)
                favicon_png_path.unlink()  # Remove temporary PNG
                print(f"  ✅ Saved favicon: {favicon_path}")
            except subprocess.CalledProcessError:
                print(f"  ⚠️  ICO conversion failed, kept PNG: {favicon_png_path}")
        else:
            print(f"  ✅ Saved favicon as PNG: {favicon_png_path}")
        
        # Generate web app icon
        web_icon = self.designer.create_base_icon(192)
        web_icon_path = self.public_dir / 'logo192.png'
        web_icon.save(web_icon_path, 'PNG')
        generated_files.append(web_icon_path)
        print(f"  ✅ Saved web app icon: {web_icon_path}")
        
        return generated_files
    
    def generate_ico_file(self, png_files: List[Path]):
        """Generate Windows ICO file using ImageMagick"""
        if not IMAGEMAGICK_AVAILABLE:
            print("  ⚠️  Skipping ICO generation - ImageMagick not available")
            return None
        
        print("🪟 Generating Windows ICO file...")
        
        # Use specific sizes for ICO (Windows standard)
        ico_sizes = [16, 24, 32, 48, 64, 128, 256]
        ico_png_files = []
        
        for size in ico_sizes:
            png_file = self.assets_dir / f'icon_{size}x{size}.png'
            if png_file.exists():
                ico_png_files.append(str(png_file))
        
        if not ico_png_files:
            print("  ❌ No PNG files found for ICO generation")
            return None
        
        ico_path = self.assets_dir / 'icon.ico'
        
        try:
            cmd = ['convert'] + ico_png_files + [str(ico_path)]
            subprocess.run(cmd, check=True)
            print(f"  ✅ Saved Windows icon: {ico_path}")
            return ico_path
        except subprocess.CalledProcessError as e:
            print(f"  ❌ ICO generation failed: {e}")
            return None
    
    def generate_icns_file(self, png_files: List[Path]):
        """Generate macOS ICNS file using ImageMagick"""
        if not IMAGEMAGICK_AVAILABLE:
            print("  ⚠️  Skipping ICNS generation - ImageMagick not available")
            return None
        
        print("🍎 Generating macOS ICNS file...")
        
        # Create iconset directory structure
        iconset_dir = self.assets_dir / 'icon.iconset'
        iconset_dir.mkdir(exist_ok=True)
        
        # macOS icon requirements
        icns_mappings = {
            16: ['icon_16x16.png'],
            32: ['icon_16x16@2x.png', 'icon_32x32.png'],
            64: ['icon_32x32@2x.png'],
            128: ['icon_128x128.png'],
            256: ['icon_128x128@2x.png', 'icon_256x256.png'],
            512: ['icon_256x256@2x.png', 'icon_512x512.png'],
            1024: ['icon_512x512@2x.png']
        }
        
        # Copy PNG files to iconset with correct naming
        for size, iconset_names in icns_mappings.items():
            source_png = self.assets_dir / f'icon_{size}x{size}.png'
            if source_png.exists():
                for iconset_name in iconset_names:
                    iconset_file = iconset_dir / iconset_name
                    iconset_file.write_bytes(source_png.read_bytes())
        
        # Generate ICNS using iconutil (macOS) or ImageMagick
        icns_path = self.assets_dir / 'icon.icns'
        
        # Try iconutil first (native macOS tool)
        try:
            subprocess.run([
                'iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)
            ], check=True)
            print(f"  ✅ Saved macOS icon (iconutil): {icns_path}")
            
            # Clean up iconset directory
            import shutil
            shutil.rmtree(iconset_dir)
            return icns_path
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  📦 iconutil not available, trying ImageMagick...")
            
            # Fallback to ImageMagick
            try:
                # Use the largest PNG files for ICNS
                large_pngs = [
                    str(self.assets_dir / f'icon_{size}x{size}.png')
                    for size in [16, 32, 64, 128, 256, 512, 1024]
                    if (self.assets_dir / f'icon_{size}x{size}.png').exists()
                ]
                
                if large_pngs:
                    cmd = ['convert'] + large_pngs + [str(icns_path)]
                    subprocess.run(cmd, check=True)
                    print(f"  ✅ Saved macOS icon (ImageMagick): {icns_path}")
                    
                    # Clean up iconset directory
                    import shutil
                    shutil.rmtree(iconset_dir)
                    return icns_path
                
            except subprocess.CalledProcessError as e:
                print(f"  ❌ ICNS generation failed: {e}")
                
                # Clean up iconset directory
                import shutil
                shutil.rmtree(iconset_dir)
                return None
    
    def generate_all_icons(self):
        """Generate all required icon formats"""
        print("🚀 Starting icon generation for Local Web Scraper...")
        print("=" * 60)
        
        # Generate PNG files
        png_files = self.generate_png_icons()
        
        # Generate platform-specific formats
        ico_file = self.generate_ico_file(png_files)
        icns_file = self.generate_icns_file(png_files)
        
        print("\n" + "=" * 60)
        print("📋 Icon Generation Summary:")
        print("=" * 60)
        
        print(f"📁 Assets directory: {self.assets_dir}")
        print(f"📁 Public directory: {self.public_dir}")
        print(f"📦 PNG files generated: {len(png_files)}")
        print(f"🪟 Windows ICO: {'✅' if ico_file else '❌'}")
        print(f"🍎 macOS ICNS: {'✅' if icns_file else '❌'}")
        
        # List all generated files
        print("\n📄 Generated files:")
        all_files = []
        
        # Check for main platform icons
        main_icons = [
            self.assets_dir / 'icon.png',
            self.assets_dir / 'icon.ico', 
            self.assets_dir / 'icon.icns'
        ]
        
        for icon_file in main_icons:
            if icon_file.exists():
                all_files.append(icon_file)
                print(f"  ✅ {icon_file.relative_to(self.base_dir)}")
            else:
                print(f"  ❌ {icon_file.relative_to(self.base_dir)} (missing)")
        
        # Check web icons
        web_icons = [
            self.public_dir / 'favicon.ico',
            self.public_dir / 'favicon.png',
            self.public_dir / 'logo192.png'
        ]
        
        for web_icon in web_icons:
            if web_icon.exists():
                all_files.append(web_icon)
                print(f"  ✅ {web_icon.relative_to(self.base_dir)}")
        
        print(f"\n🎉 Icon generation completed! Generated {len(all_files)} files.")
        
        if not ico_file or not icns_file:
            print("\n💡 Note: Install ImageMagick for full platform support:")
            print("  macOS: brew install imagemagick")
            print("  Ubuntu: sudo apt-get install imagemagick")
            print("  Windows: choco install imagemagick")
        
        return all_files


def main():
    """Main function to generate all icons"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate icons for Local Web Scraper app")
    parser.add_argument("--base-dir", type=str, 
                       default="/Users/rr/MLOPS/Crawler_max/desktop-scraper",
                       help="Base directory of the desktop app")
    parser.add_argument("--install-deps", action="store_true",
                       help="Install required dependencies")
    
    args = parser.parse_args()
    
    if args.install_deps:
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow'])
    
    # Verify base directory exists
    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f"❌ Base directory not found: {base_dir}")
        sys.exit(1)
    
    # Generate icons
    generator = IconGenerator(str(base_dir))
    generated_files = generator.generate_all_icons()
    
    print(f"\n✨ Ready! Your Local Web Scraper app now has custom icons.")
    print("🔧 Next steps:")
    print("  1. Build the app: npm run build")
    print("  2. Package the app: npm run package")
    print("  3. Test the icons on each platform")


if __name__ == "__main__":
    main()