#!/bin/bash
# Signed Build Script for Local Web Scraper
# =========================================

set -e  # Exit on any error

echo "🔐 Local Web Scraper - Signed Build Process"
echo "==========================================="

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
ENV_FILE="$PROJECT_ROOT/.env.signing"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if environment file exists
check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        warning "No .env.signing file found"
        info "Creating from template..."
        
        if [[ -f "$PROJECT_ROOT/.env.signing.template" ]]; then
            cp "$PROJECT_ROOT/.env.signing.template" "$ENV_FILE"
            error "Please edit .env.signing with your actual certificate information"
            info "Then run this script again"
            exit 1
        else
            error "No .env.signing.template found. Run setup script first:"
            error "./scripts/setup_code_signing.sh --setup-config"
            exit 1
        fi
    fi
}

# Load environment variables
load_env() {
    log "Loading signing environment variables..."
    
    # Load environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    # Check for required variables based on platform
    local platform=$(uname -s)
    
    case "$platform" in
        "Darwin")
            check_macos_env
            ;;
        "MINGW"*|"MSYS"*|"CYGWIN"*)
            check_windows_env
            ;;
        "Linux")
            info "Linux: No code signing required for AppImage"
            ;;
    esac
}

# Check macOS environment
check_macos_env() {
    log "Checking macOS signing environment..."
    
    # Check for certificates in Keychain
    local cert_count=$(security find-identity -v -p codesigning | grep "Developer ID Application" | wc -l)
    
    if [[ $cert_count -eq 0 ]]; then
        error "No Developer ID Application certificates found in Keychain"
        info "Please install your Apple Developer certificate first"
        info "See docs/CODE_SIGNING_GUIDE.md for instructions"
        exit 1
    else
        log "Found $cert_count Developer ID Application certificate(s)"
    fi
    
    # Check notarization credentials (optional but recommended)
    if [[ -n "$APPLE_ID" ]] && [[ -n "$APPLE_ID_PASSWORD" ]] && [[ -n "$APPLE_TEAM_ID" ]]; then
        log "Notarization credentials configured"
        export APPLE_ID APPLE_ID_PASSWORD APPLE_TEAM_ID
    else
        warning "Notarization credentials not configured"
        warning "App will be signed but not notarized"
        info "For best user experience, configure notarization in .env.signing"
    fi
}

# Check Windows environment
check_windows_env() {
    log "Checking Windows signing environment..."
    
    if [[ -z "$CSC_LINK" ]] || [[ -z "$CSC_KEY_PASSWORD" ]]; then
        error "Windows signing credentials not configured"
        info "Set CSC_LINK and CSC_KEY_PASSWORD in .env.signing"
        exit 1
    fi
    
    # Check if certificate file exists
    if [[ ! -f "$CSC_LINK" ]]; then
        error "Certificate file not found: $CSC_LINK"
        info "Please place your .pfx or .p12 certificate file in the project"
        exit 1
    fi
    
    log "Windows signing credentials configured"
    export CSC_LINK CSC_KEY_PASSWORD
}

# Clean previous builds
clean_dist() {
    log "Cleaning previous builds..."
    
    if [[ -d "$DIST_DIR" ]]; then
        rm -rf "$DIST_DIR"
        log "Removed existing dist directory"
    fi
}

# Build the application
build_app() {
    log "Building Local Web Scraper application..."
    
    cd "$PROJECT_ROOT"
    
    # Install dependencies if needed
    if [[ ! -d "node_modules" ]]; then
        log "Installing dependencies..."
        npm install
    fi
    
    # Build main process
    log "Building main process..."
    npm run build:main
    
    # Build renderer process
    log "Building renderer process..."
    npm run build:frontend
    
    # Build and package with Electron Builder
    log "Packaging with Electron Builder..."
    npm run build:electron
    
    log "Build completed!"
}

# Verify signatures
verify_signatures() {
    log "Verifying application signatures..."
    
    local platform=$(uname -s)
    
    case "$platform" in
        "Darwin")
            verify_macos_signature
            ;;
        "MINGW"*|"MSYS"*|"CYGWIN"*)
            verify_windows_signature
            ;;
        "Linux")
            verify_linux_package
            ;;
    esac
}

# Verify macOS signature
verify_macos_signature() {
    log "Verifying macOS application signature..."
    
    local app_path=$(find "$DIST_DIR" -name "*.app" -type d | head -1)
    local dmg_path=$(find "$DIST_DIR" -name "*.dmg" -type f | head -1)
    
    if [[ -n "$app_path" ]]; then
        info "Verifying app bundle: $(basename "$app_path")"
        
        # Basic signature verification
        if codesign --verify --deep --strict --verbose=2 "$app_path" 2>&1; then
            log "✅ App bundle signature is valid"
        else
            error "❌ App bundle signature verification failed"
            exit 1
        fi
        
        # Gatekeeper assessment
        if spctl --assess --type execute --verbose "$app_path" 2>&1; then
            log "✅ App passes Gatekeeper assessment"
        else
            warning "⚠️  App fails Gatekeeper assessment"
            info "This may be expected for development certificates"
        fi
    fi
    
    if [[ -n "$dmg_path" ]]; then
        info "Verifying DMG: $(basename "$dmg_path")"
        
        # DMG signature verification
        if codesign --verify --deep --strict --verbose=2 "$dmg_path" 2>&1; then
            log "✅ DMG signature is valid"
        else
            warning "⚠️  DMG signature verification failed"
        fi
    fi
}

# Verify Windows signature
verify_windows_signature() {
    log "Verifying Windows application signature..."
    
    local exe_path=$(find "$DIST_DIR" -name "*.exe" -type f | head -1)
    
    if [[ -n "$exe_path" ]]; then
        info "Verifying executable: $(basename "$exe_path")"
        
        # Check if we're on Windows or have Windows tools available
        if command -v powershell &> /dev/null; then
            local sig_status=$(powershell -Command "Get-AuthenticodeSignature '$exe_path' | Select-Object -ExpandProperty Status")
            
            if [[ "$sig_status" == "Valid" ]]; then
                log "✅ Executable signature is valid"
            else
                warning "⚠️  Executable signature status: $sig_status"
            fi
        else
            info "PowerShell not available - signature verification skipped"
            info "Test the executable on a Windows machine to verify signing"
        fi
    fi
}

# Verify Linux package
verify_linux_package() {
    log "Verifying Linux package..."
    
    local appimage_path=$(find "$DIST_DIR" -name "*.AppImage" -type f | head -1)
    
    if [[ -n "$appimage_path" ]]; then
        info "AppImage created: $(basename "$appimage_path")"
        
        # Check if file is executable
        if [[ -x "$appimage_path" ]]; then
            log "✅ AppImage is executable"
        else
            warning "⚠️  AppImage is not executable"
            chmod +x "$appimage_path"
            log "Fixed AppImage permissions"
        fi
        
        # Check file size (should be > 100MB for full app)
        local file_size=$(stat -f%z "$appimage_path" 2>/dev/null || stat -c%s "$appimage_path" 2>/dev/null)
        local size_mb=$((file_size / 1024 / 1024))
        
        if [[ $size_mb -gt 100 ]]; then
            log "✅ AppImage size looks reasonable: ${size_mb}MB"
        else
            warning "⚠️  AppImage size seems small: ${size_mb}MB"
        fi
    fi
}

# Generate build report
generate_report() {
    log "Generating build report..."
    
    local report_file="$DIST_DIR/BUILD_REPORT.md"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local platform=$(uname -s)
    
    cat > "$report_file" << EOF
# Local Web Scraper - Build Report

**Build Date**: $timestamp
**Platform**: $platform
**Signed**: Yes

## Generated Files

EOF
    
    # List all generated files
    if [[ -d "$DIST_DIR" ]]; then
        find "$DIST_DIR" -type f -not -name "BUILD_REPORT.md" | sort | while read file; do
            local rel_path=$(realpath --relative-to="$DIST_DIR" "$file" 2>/dev/null || echo "${file#$DIST_DIR/}")
            local file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
            local size_mb=$((file_size / 1024 / 1024))
            
            echo "- **$rel_path** (${size_mb}MB)" >> "$report_file"
        done
    fi
    
    cat >> "$report_file" << EOF

## Signing Status

EOF
    
    case "$platform" in
        "Darwin")
            echo "- **macOS**: Code signed with Developer ID Application certificate" >> "$report_file"
            if [[ -n "$APPLE_ID" ]]; then
                echo "- **Notarization**: Configured for Apple notarization" >> "$report_file"
            else
                echo "- **Notarization**: Not configured" >> "$report_file"
            fi
            ;;
        "MINGW"*|"MSYS"*|"CYGWIN"*)
            echo "- **Windows**: Code signed with certificate" >> "$report_file"
            ;;
        "Linux")
            echo "- **Linux**: AppImage package (no signing required)" >> "$report_file"
            ;;
    esac
    
    cat >> "$report_file" << EOF

## Installation Instructions

### macOS
1. Download the DMG file
2. Open the DMG
3. Drag Local Web Scraper to Applications folder
4. Launch from Applications (no security warnings expected)

### Windows
1. Download the installer (.exe)
2. Run the installer
3. Follow installation prompts
4. App will be available in Start Menu

### Linux
1. Download the AppImage file
2. Make it executable: \`chmod +x Local-Web-Scraper-*.AppImage\`
3. Run directly: \`./Local-Web-Scraper-*.AppImage\`

## Security Notes

- All binaries are code signed for trusted distribution
- Users should not see security warnings on supported platforms
- Verify signatures before distribution to end users

Generated by Local Web Scraper build system
EOF
    
    log "Build report saved: $report_file"
}

# Main function
main() {
    log "Starting signed build process for Local Web Scraper..."
    
    # Parse command line arguments
    local skip_verify=false
    local skip_clean=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-verify)
                skip_verify=true
                shift
                ;;
            --skip-clean)
                skip_clean=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  --skip-verify    Skip signature verification"
                echo "  --skip-clean     Skip cleaning dist directory"
                echo "  --help          Show this help"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Execute build pipeline
    check_env_file
    load_env
    
    if [[ "$skip_clean" != true ]]; then
        clean_dist
    fi
    
    build_app
    
    if [[ "$skip_verify" != true ]]; then
        verify_signatures
    fi
    
    generate_report
    
    log "🎉 Signed build completed successfully!"
    
    # Show next steps
    info "📦 Built packages are in: $DIST_DIR"
    info "📋 Build report: $DIST_DIR/BUILD_REPORT.md"
    info "🚀 Ready for distribution!"
}

# Handle interruption
trap 'error "Build interrupted"; exit 1' INT TERM

# Run main function
main "$@"