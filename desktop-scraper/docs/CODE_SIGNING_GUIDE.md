# Code Signing Guide for Local Web Scraper

This guide covers setting up code signing for trusted distribution of the Local Web Scraper desktop application across Windows, macOS, and Linux platforms.

## 🎯 Overview

Code signing is essential for:
- **User Trust**: Eliminates security warnings when users run your app
- **Platform Compliance**: Required for app store distribution
- **Professional Distribution**: Establishes developer identity and authenticity

## 📋 Current Status

### ✅ What's Configured
- **Electron Builder Setup**: Ready for code signing on all platforms
- **Build Configuration**: Package.json configured with signing parameters
- **Entitlements**: macOS entitlements file created for proper sandboxing
- **Environment Template**: Template for secure credential management

### ❌ What's Missing
- **Certificates**: No production certificates installed
- **Apple Developer Account**: Required for macOS signing ($99/year)
- **Windows Certificate**: Required for Windows signing ($200-600/year)

## 🍎 macOS Code Signing

### Prerequisites
1. **Apple Developer Program Membership** - $99/year
2. **Xcode Command Line Tools** - `xcode-select --install`
3. **Valid Apple ID** with Two-Factor Authentication

### Step 1: Join Apple Developer Program
1. Visit [Apple Developer Portal](https://developer.apple.com/programs/)
2. Enroll in the Apple Developer Program
3. Complete identity verification (can take 24-48 hours)

### Step 2: Create Developer ID Application Certificate
1. Open **Keychain Access** on your Mac
2. Go to **Keychain Access > Certificate Assistant > Request a Certificate From a Certificate Authority**
3. Fill in your email and name, select "Saved to disk"
4. Save the Certificate Signing Request (CSR) file

5. In Apple Developer Portal:
   - Go to **Certificates, Identifiers & Profiles**
   - Click **Certificates** → **Create a Certificate**
   - Select **Developer ID Application**
   - Upload your CSR file
   - Download the certificate

6. Double-click the downloaded certificate to install it in Keychain

### Step 3: Configure Environment
Create `.env.signing` file:
```bash
# macOS Code Signing
CSC_IDENTITY_AUTO_DISCOVERY=true

# For notarization (recommended for macOS 10.15+)
APPLE_ID=your-apple-id@email.com
APPLE_ID_PASSWORD=app-specific-password
APPLE_TEAM_ID=YOUR_TEAM_ID
```

### Step 4: Setup App-Specific Password
1. Go to [Apple ID Account Page](https://appleid.apple.com/)
2. Sign in and go to **Security** section
3. Generate an app-specific password for "Local Web Scraper"
4. Use this password in `APPLE_ID_PASSWORD`

### Step 5: Test macOS Signing
```bash
# Build with signing
npm run build:electron

# Verify signing
codesign --verify --deep --strict --verbose=2 dist/mac/Local\ Web\ Scraper.app

# Test Gatekeeper
spctl --assess --type execute --verbose dist/mac/Local\ Web\ Scraper.app
```

## 🪟 Windows Code Signing

### Prerequisites
1. **Code Signing Certificate** from a trusted Certificate Authority
2. **Windows 10/11** or Windows Server for testing

### Step 1: Choose Certificate Type

#### Extended Validation (EV) Certificate - Recommended
- **Cost**: $300-600/year
- **Benefit**: No SmartScreen warnings immediately
- **Providers**: DigiCert, GlobalSign, Sectigo
- **Validation**: Requires business verification

#### Standard Code Signing Certificate
- **Cost**: $200-400/year
- **Benefit**: Basic code signing, requires reputation building
- **SmartScreen**: May show warnings until reputation is established

### Step 2: Purchase Certificate
1. Choose a Certificate Authority:
   - **DigiCert** (recommended for EV)
   - **GlobalSign**
   - **Sectigo**
   - **SSL.com**

2. Complete business verification process
3. Download certificate as `.pfx` or `.p12` file

### Step 3: Configure Environment
Add to `.env.signing`:
```bash
# Windows Code Signing
CSC_LINK=path/to/your-certificate.pfx
CSC_KEY_PASSWORD=your-certificate-password

# Alternative: Certificate in Windows certificate store
# WIN_CSC_LINK=path/to/certificate.p7b
# WIN_CSC_KEY_PASSWORD=your-password
```

### Step 4: Test Windows Signing
```bash
# Build with signing
npm run build:electron

# Verify on Windows
Get-AuthenticodeSignature dist/win-unpacked/Local\ Web\ Scraper.exe
```

## 🐧 Linux Distribution

### AppImage (Current)
- **No signing required** for basic distribution
- **GPG signing** optional for package integrity
- **Already configured** and working

### Optional: GPG Signing
```bash
# Generate GPG key
gpg --gen-key

# Sign AppImage
gpg --detach-sign --armor dist/Local\ Web\ Scraper-1.0.0.AppImage

# Verify
gpg --verify dist/Local\ Web\ Scraper-1.0.0.AppImage.asc
```

## 🔧 Configuration Files

### Package.json Build Configuration
```json
{
  "build": {
    "mac": {
      "hardenedRuntime": true,
      "gatekeeperAssess": false,
      "entitlements": "assets/entitlements.mac.plist",
      "entitlementsInherit": "assets/entitlements.mac.plist",
      "notarize": {
        "teamId": "YOUR_TEAM_ID"
      }
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
```

### macOS Entitlements (assets/entitlements.mac.plist)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
  </dict>
</plist>
```

## 🔐 Environment Variables Template

Create `.env.signing` based on `.env.signing.template`:

```bash
# Copy template
cp .env.signing.template .env.signing

# Edit with your actual values
# Note: .env.signing is in .gitignore for security
```

## 🚀 Building Signed Applications

### Development Build (unsigned)
```bash
npm run build:electron
```

### Production Build (signed)
```bash
# Load signing environment
source .env.signing

# Build with signing
npm run build:electron
```

### Automated CI/CD
```bash
# GitHub Actions, Azure Pipelines, etc.
# Set environment variables in CI secrets
CSC_LINK: ${{ secrets.CSC_LINK }}
CSC_KEY_PASSWORD: ${{ secrets.CSC_KEY_PASSWORD }}
APPLE_ID: ${{ secrets.APPLE_ID }}
APPLE_ID_PASSWORD: ${{ secrets.APPLE_ID_PASSWORD }}
```

## 🧪 Testing Signed Applications

### macOS Testing
```bash
# Verify code signature
codesign --verify --deep --strict --verbose=2 "dist/mac/Local Web Scraper.app"

# Check Gatekeeper assessment
spctl --assess --type execute --verbose "dist/mac/Local Web Scraper.app"

# Test notarization status
spctl --assess --type install --context context:primary-signature --verbose "dist/Local Web Scraper-1.0.0.dmg"
```

### Windows Testing
```powershell
# Verify signature
Get-AuthenticodeSignature "dist\Local Web Scraper Setup 1.0.0.exe"

# Check certificate details
Get-AuthenticodeSignature "dist\Local Web Scraper Setup 1.0.0.exe" | Select-Object *
```

## 💰 Cost Summary

| Platform | Certificate Type | Annual Cost | Setup Time |
|----------|------------------|-------------|------------|
| macOS | Apple Developer ID | $99 | 2-3 hours |
| Windows (Standard) | Code Signing | $200-400 | 1-2 hours |
| Windows (EV) | EV Code Signing | $300-600 | 2-4 hours |
| Linux | GPG (optional) | Free | 30 minutes |

## 🔍 Troubleshooting

### Common macOS Issues
- **"No identity found"**: Certificate not in Keychain or expired
- **"Operation not permitted"**: Enable Developer Tools in Security settings
- **Notarization fails**: Check Apple ID credentials and team ID

### Common Windows Issues
- **"Certificate not found"**: Check file path and password
- **"Invalid certificate"**: Ensure certificate is for code signing
- **SmartScreen warnings**: Expected for new certificates, improves with reputation

### Common Build Issues
- **Environment variables not loaded**: Use `source .env.signing`
- **Certificate permissions**: Ensure proper file permissions
- **Network issues**: Check firewall settings for notarization

## 📚 Additional Resources

- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Windows Code Signing Best Practices](https://docs.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-best-practices)
- [Electron Builder Code Signing](https://www.electron.build/code-signing)
- [Certificate Authorities Comparison](https://www.ssl.com/certificates/code-signing/)

## 🎯 Next Steps

1. **Decide on certificate strategy** based on budget and timeline
2. **Obtain necessary certificates** and developer accounts
3. **Configure environment variables** with actual credentials
4. **Test signing process** with development builds
5. **Document internal procedures** for team members
6. **Set up CI/CD integration** for automated signing

Remember: Code signing is an investment in user trust and professional distribution. While the setup requires time and cost, it's essential for serious application deployment.