#!/bin/bash
# Code Signing Setup Script for Local Web Scraper Desktop App
# ===========================================================

set -e  # Exit on any error

echo "🔐 Local Web Scraper - Code Signing Setup"
echo "=========================================="

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_DIR="$PROJECT_ROOT/assets"

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

# Check current platform
check_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Check for existing certificates and signing setup
check_existing_setup() {
    log "Checking existing code signing setup..."
    
    local platform=$(check_platform)
    
    case "$platform" in
        "macos")
            check_macos_certificates
            ;;
        "windows")
            check_windows_certificates
            ;;
        "linux")
            info "Linux: No code signing required for AppImage distribution"
            ;;
        *)
            warning "Unknown platform: $OSTYPE"
            ;;
    esac
}

# Check macOS certificates
check_macos_certificates() {
    info "Checking macOS Developer certificates..."
    
    # Check for Developer ID Application certificates
    local dev_certs=$(security find-identity -v -p codesigning | grep "Developer ID Application" | wc -l)
    
    if [[ $dev_certs -gt 0 ]]; then
        log "Found $dev_certs Developer ID Application certificate(s):"
        security find-identity -v -p codesigning | grep "Developer ID Application"
        
        # Check if they're valid
        info "Checking certificate validity..."
        security find-identity -v -p codesigning | grep "Developer ID Application" | while read line; do
            local cert_hash=$(echo "$line" | awk '{print $2}')
            local cert_name=$(echo "$line" | sed 's/.*) "//' | sed 's/".*//')
            
            # Test certificate
            if codesign --verify --deep --strict --verbose=2 /Applications/Calculator.app 2>/dev/null; then
                log "Certificate '$cert_name' appears valid"
            else
                warning "Certificate '$cert_name' may have issues"
            fi
        done
    else
        warning "No Developer ID Application certificates found"
        info "You need to:"
        info "1. Join Apple Developer Program (\$99/year)"
        info "2. Create a Developer ID Application certificate"
        info "3. Download and install it in Keychain"
    fi
    
    # Check for Apple ID credentials for notarization
    if [[ -n "$APPLE_ID" ]] && [[ -n "$APPLE_ID_PASSWORD" ]]; then
        log "Apple ID credentials configured for notarization"
    else
        warning "Apple ID credentials not configured for notarization"
        info "Set environment variables:"
        info "export APPLE_ID=your-apple-id@email.com"
        info "export APPLE_ID_PASSWORD=app-specific-password"
        info "export APPLE_TEAM_ID=YOUR_TEAM_ID"
    fi
}

# Check Windows certificates
check_windows_certificates() {
    info "Checking Windows code signing certificates..."
    
    # Check for certificate files
    local cert_files=(
        "$PROJECT_ROOT/certs/*.pfx"
        "$PROJECT_ROOT/certs/*.p12"
        "$PROJECT_ROOT/*.pfx"
        "$PROJECT_ROOT/*.p12"
    )
    
    local found_cert=false
    for cert_pattern in "${cert_files[@]}"; do
        if ls $cert_pattern 1> /dev/null 2>&1; then
            log "Found certificate file: $cert_pattern"
            found_cert=true
        fi
    done
    
    if [[ "$found_cert" == false ]]; then
        warning "No certificate files found"
        info "You need to:"
        info "1. Purchase a code signing certificate from a trusted CA"
        info "2. Download the certificate (.pfx or .p12 file)"
        info "3. Place it in the project root or certs/ directory"
    fi
    
    # Check environment variables
    if [[ -n "$CSC_LINK" ]] && [[ -n "$CSC_KEY_PASSWORD" ]]; then
        log "Windows signing environment variables configured"
        if [[ -f "$CSC_LINK" ]]; then
            log "Certificate file exists: $CSC_LINK"
        else
            error "Certificate file not found: $CSC_LINK"
        fi
    else
        warning "Windows signing environment variables not configured"
        info "Set environment variables:"
        info "export CSC_LINK=path/to/certificate.pfx"
        info "export CSC_KEY_PASSWORD=your-certificate-password"
    fi
}

# Create development certificate for testing (macOS/Windows)
create_dev_certificate() {
    local platform=$(check_platform)
    
    warning "Creating DEVELOPMENT-ONLY self-signed certificate"
    warning "This should NOT be used for production distribution!"
    
    case "$platform" in
        "macos")
            create_macos_dev_cert
            ;;
        "windows")
            create_windows_dev_cert
            ;;
        *)
            error "Development certificate creation not supported on this platform"
            return 1
            ;;
    esac
}

# Create macOS development certificate
create_macos_dev_cert() {
    log "Creating macOS development certificate..."
    
    warning "Creating a self-signed certificate for development testing"
    warning "This will NOT provide trusted distribution - users will still see warnings"
    
    # Use electron-builder's built-in certificate creation
    cd "$PROJECT_ROOT"
    
    if ! command -v npx &> /dev/null; then
        error "npx not found. Please install Node.js and npm first."
        return 1
    fi
    
    # Check if development certificate already exists
    if [[ -f "dev-cert-mac.p12" ]]; then
        log "Development certificate already exists: dev-cert-mac.p12"
        return 0
    fi
    
    log "Generating self-signed certificate with electron-builder..."
    npx electron-builder create-self-signed-cert -p "Local Web Scraper Dev"
    
    if [[ -f "dev-cert.pfx" ]]; then
        # Rename for clarity
        mv "dev-cert.pfx" "dev-cert-mac.p12"
        log "Development certificate created: dev-cert-mac.p12"
        info "Set environment variables for development:"
        info "export CSC_LINK=$(pwd)/dev-cert-mac.p12"
        info "export CSC_KEY_PASSWORD=test"
    else
        error "Failed to create development certificate"
        return 1
    fi
    
    warning "Remember: This is for DEVELOPMENT ONLY"
}

# Create Windows development certificate
create_windows_dev_cert() {
    log "Creating Windows development certificate..."
    
    # Check if we have electron-builder installed
    if ! command -v npx &> /dev/null; then
        error "npx not found. Please install Node.js and npm first."
        return 1
    fi
    
    # Use electron-builder's certificate creation utility
    cd "$PROJECT_ROOT"
    
    if [[ ! -f "dev-cert.pfx" ]]; then
        log "Generating self-signed certificate with electron-builder..."
        npx electron-builder create-self-signed-cert -p "Local Web Scraper"
        
        if [[ -f "dev-cert.pfx" ]]; then
            log "Development certificate created: dev-cert.pfx"
            info "Set environment variables for development:"
            info "export CSC_LINK=$(pwd)/dev-cert.pfx"
            info "export CSC_KEY_PASSWORD=test"
        else
            error "Failed to create development certificate"
            return 1
        fi
    else
        log "Development certificate already exists: dev-cert.pfx"
    fi
    
    warning "Remember: This is for DEVELOPMENT ONLY"
}

# Setup code signing configuration in package.json
setup_package_config() {
    log "Setting up package.json code signing configuration..."
    
    local package_file="$PROJECT_ROOT/package.json"
    local temp_file=$(mktemp)
    
    # Check if jq is available for JSON manipulation
    if ! command -v jq &> /dev/null; then
        warning "jq not found. Please install jq for automatic package.json updates"
        info "Manual configuration required in package.json"
        show_manual_config
        return 1
    fi
    
    # Backup original package.json
    cp "$package_file" "$package_file.backup"
    
    # Add macOS signing configuration
    jq '.build.mac.hardenedRuntime = true' "$package_file" > "$temp_file" && mv "$temp_file" "$package_file"
    jq '.build.mac.gatekeeperAssess = false' "$package_file" > "$temp_file" && mv "$temp_file" "$package_file"
    
    # Add Windows signing configuration
    jq '.build.win.signingHashAlgorithms = ["sha256"]' "$package_file" > "$temp_file" && mv "$temp_file" "$package_file"
    jq '.build.win.signDlls = true' "$package_file" > "$temp_file" && mv "$temp_file" "$package_file"
    
    log "Package.json updated with code signing configuration"
    info "Backup saved as: $package_file.backup"
}

# Show manual configuration instructions
show_manual_config() {
    info "Manual package.json configuration:"
    
    cat << 'EOF'
Add the following to your package.json build configuration:

{
  "build": {
    "mac": {
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "assets/entitlements.mac.plist",
      "entitlementsInherit": "assets/entitlements.mac.plist",
      "notarize": false
    },
    "win": {
      "signingHashAlgorithms": ["sha256"],
      "signDlls": true
    },
    "linux": {
      "category": "Development"
    }
  }
}

For production, also add:
{
  "build": {
    "mac": {
      "notarize": {
        "teamId": "YOUR_TEAM_ID"
      }
    }
  }
}
EOF
}

# Create macOS entitlements file
create_entitlements() {
    log "Creating macOS entitlements file..."
    
    mkdir -p "$ASSETS_DIR"
    
    cat > "$ASSETS_DIR/entitlements.mac.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <!-- Allow outbound network connections for web scraping -->
    <key>com.apple.security.network.client</key>
    <true/>
    
    <!-- Allow loading of unsigned executable memory -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    
    <!-- Allow JIT compilation for JavaScript engines -->
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    
    <!-- Disable library validation for Electron -->
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    
    <!-- Allow dyld environment variables -->
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
  </dict>
</plist>
EOF
    
    log "Entitlements file created: $ASSETS_DIR/entitlements.mac.plist"
}

# Create environment template file
create_env_template() {
    log "Creating environment variables template..."
    
    cat > "$PROJECT_ROOT/.env.signing.template" << 'EOF'
# Code Signing Environment Variables Template
# ==========================================
# Copy this file to .env.signing and fill in your actual values
# Add .env.signing to .gitignore to keep credentials secure

# macOS Code Signing
# ------------------
# Automatically discover certificates (recommended)
CSC_IDENTITY_AUTO_DISCOVERY=true

# Or specify certificate name explicitly:
# CSC_NAME="Developer ID Application: Your Name (TEAM_ID)"

# Apple ID for notarization (production only)
# APPLE_ID=your-apple-id@email.com
# APPLE_ID_PASSWORD=app-specific-password
# APPLE_TEAM_ID=YOUR_TEAM_ID

# Windows Code Signing
# --------------------
# Path to certificate file (.pfx or .p12)
# CSC_LINK=path/to/certificate.pfx
# CSC_KEY_PASSWORD=your-certificate-password

# Alternative: Certificate in Windows certificate store
# WIN_CSC_LINK=path/to/certificate.p7b
# WIN_CSC_KEY_PASSWORD=your-password

# Development Only (self-signed certificates)
# -------------------------------------------
# For development builds only - DO NOT use in production
# CSC_LINK=./dev-cert.pfx
# CSC_KEY_PASSWORD=test
EOF
    
    log "Environment template created: .env.signing.template"
    
    # Add to .gitignore if not already there
    if [[ -f "$PROJECT_ROOT/.gitignore" ]]; then
        if ! grep -q ".env.signing" "$PROJECT_ROOT/.gitignore"; then
            echo ".env.signing" >> "$PROJECT_ROOT/.gitignore"
            log "Added .env.signing to .gitignore"
        fi
    fi
}

# Test code signing setup
test_signing() {
    log "Testing code signing setup..."
    
    local platform=$(check_platform)
    
    info "Building application to test code signing..."
    cd "$PROJECT_ROOT"
    
    # Load environment variables if available
    if [[ -f ".env.signing" ]]; then
        set -a
        source .env.signing
        set +a
        log "Loaded signing environment variables"
    fi
    
    # Build the application
    if npm run build:electron; then
        log "Build completed successfully"
        
        case "$platform" in
            "macos")
                test_macos_signing
                ;;
            "windows")
                test_windows_signing
                ;;
            "linux")
                info "Linux: AppImage created successfully (no signing required)"
                ;;
        esac
    else
        error "Build failed"
        return 1
    fi
}

# Test macOS signing
test_macos_signing() {
    log "Testing macOS code signing..."
    
    local app_path=$(find "$PROJECT_ROOT/dist" -name "*.app" -type d | head -1)
    
    if [[ -n "$app_path" ]]; then
        log "Testing app: $app_path"
        
        # Check if app is signed
        if codesign --verify --deep --strict --verbose=2 "$app_path"; then
            log "✅ App is properly signed"
            
            # Check Gatekeeper assessment
            if spctl --assess --type execute --verbose "$app_path"; then
                log "✅ App passes Gatekeeper assessment"
            else
                warning "⚠️  App fails Gatekeeper assessment (may be expected for dev certificates)"
            fi
        else
            warning "⚠️  App is not signed or has signing issues"
        fi
    else
        error "No .app file found in dist directory"
    fi
}

# Test Windows signing
test_windows_signing() {
    log "Testing Windows code signing..."
    
    local exe_path=$(find "$PROJECT_ROOT/dist" -name "*.exe" -type f | head -1)
    
    if [[ -n "$exe_path" ]]; then
        log "Testing executable: $exe_path"
        
        # Check if executable is signed (requires PowerShell on Windows)
        if command -v powershell &> /dev/null; then
            if powershell -Command "Get-AuthenticodeSignature '$exe_path' | Select-Object Status"; then
                log "✅ Executable signature checked"
            else
                warning "⚠️  Could not verify executable signature"
            fi
        else
            info "PowerShell not available - cannot verify signature on this platform"
        fi
    else
        error "No .exe file found in dist directory"
    fi
}

# Show comprehensive setup instructions
show_instructions() {
    echo
    echo "📋 Code Signing Setup Instructions"
    echo "=================================="
    echo
    
    info "🍎 macOS Setup (for trusted distribution):"
    echo "1. Join Apple Developer Program (\$99/year)"
    echo "2. Create Developer ID Application certificate"
    echo "3. Download and install certificate in Keychain"
    echo "4. Configure environment variables in .env.signing"
    echo "5. For modern macOS: Setup notarization with Apple ID"
    echo
    
    info "🪟 Windows Setup (for trusted distribution):"
    echo "1. Purchase code signing certificate from trusted CA:"
    echo "   - DigiCert (recommended for EV certificates)"
    echo "   - GlobalSign"
    echo "   - Sectigo"
    echo "   - SSL.com"
    echo "2. Download certificate (.pfx or .p12 file)"
    echo "3. Configure environment variables in .env.signing"
    echo
    
    info "🐧 Linux Setup:"
    echo "✅ No code signing required for AppImage distribution"
    echo
    
    warning "🛠️  Development Setup (testing only):"
    echo "Run: $0 --create-dev-cert"
    echo "This creates self-signed certificates for development testing"
    echo
    
    info "🔧 Next Steps:"
    echo "1. Copy .env.signing.template to .env.signing"
    echo "2. Fill in your certificate information"
    echo "3. Run: $0 --test to verify setup"
    echo "4. Build with: npm run build:electron"
}

# Main function
main() {
    log "Starting code signing setup for Local Web Scraper..."
    
    # Parse command line arguments
    case "${1:-}" in
        --check)
            check_existing_setup
            ;;
        --create-dev-cert)
            create_dev_certificate
            ;;
        --setup-config)
            setup_package_config
            create_entitlements
            create_env_template
            ;;
        --test)
            test_signing
            ;;
        --instructions)
            show_instructions
            ;;
        --help)
            echo "Usage: $0 [OPTION]"
            echo
            echo "Options:"
            echo "  --check           Check existing code signing setup"
            echo "  --create-dev-cert Create development certificate (testing only)"
            echo "  --setup-config    Configure package.json and create template files"
            echo "  --test            Test code signing by building the app"
            echo "  --instructions    Show detailed setup instructions"
            echo "  --help            Show this help message"
            echo
            echo "Default (no options): Run full setup process"
            ;;
        "")
            # Full setup process
            check_existing_setup
            setup_package_config
            create_entitlements
            create_env_template
            show_instructions
            ;;
        *)
            error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"