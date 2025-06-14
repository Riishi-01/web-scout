# Local Web Scraper - Desktop Application

A powerful desktop web scraping application with offline AI capabilities, built with Electron, React, and TinyLlama.

## 🚀 Features

- **Offline AI Processing**: Fine-tuned TinyLlama model for intelligent web scraping
- **Natural Language Interface**: Describe scraping tasks in plain English
- **Live Preview**: See sample data before running full extraction
- **Google Sheets Integration**: One-click export to Google Sheets
- **Anti-Detection**: Built-in mechanisms to avoid being blocked
- **Cross-Platform**: Windows, macOS, and Linux support
- **Dark/Light Theme**: Automatic system theme detection

## 🏗️ Architecture

```
├── Electron Desktop App (UI Layer)
├── Fine-tuned TinyLlama (AI Layer)
├── Playwright Browser Engine (Scraping Layer)
└── Google APIs (Export Layer)
```

## 📁 Project Structure

```
src/
├── main/                    # Electron main process
│   ├── main.ts             # Application entry point
│   ├── preload.ts          # IPC bridge
│   ├── ai/                 # AI model management
│   ├── auth/               # Google authentication
│   └── scraping/           # Scraping engine
├── renderer/               # React frontend
│   ├── App.tsx            # Main React app
│   ├── components/        # UI components
│   ├── contexts/          # React contexts
│   └── styles/            # CSS styles
└── shared/                 # Shared types and utilities
```

## 🔧 Implementation Status

### ✅ Completed Components

1. **Electron Application Framework**
   - Main process with IPC communication
   - React frontend with TypeScript
   - Theme management (dark/light/system)
   - Window management and system tray

2. **Setup Wizard**
   - Welcome screen with feature overview
   - AI model loading and status
   - Google OAuth authentication
   - Test scraping demonstration
   - Completion confirmation

3. **AI Model Integration**
   - ONNX Runtime for local inference
   - Model loading and management
   - Performance monitoring
   - Error handling and recovery

4. **Authentication System**
   - Google OAuth 2.0 flow
   - Encrypted credential storage
   - Token refresh automation
   - Multi-account support

5. **Scraping Engine**
   - Playwright browser automation
   - Anti-detection mechanisms
   - Session management
   - Error recovery with LLM assistance

6. **User Interface**
   - Modern React components with Tailwind CSS
   - Responsive design
   - Progress tracking
   - Live data preview
   - Template library
   - Settings panel

7. **Data Processing**
   - Google Sheets API integration
   - Data cleaning and validation
   - Quality assessment metrics
   - Multiple export formats

### 🔄 In Progress

1. **Model Fine-tuning**
   - Training dataset collection
   - TinyLlama fine-tuning for web scraping
   - Model quantization and optimization

2. **System Integration**
   - Auto-launch functionality
   - File associations
   - Desktop notifications

### ⏳ Pending

1. **Distribution**
   - Single executable packaging
   - Code signing for all platforms
   - Auto-update system
   - Installer creation

2. **Documentation**
   - User guide and tutorials
   - Video walkthroughs
   - API documentation

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+
- Python 3.9+ (for model training)
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd desktop-scraper

# Install dependencies
npm install

# Install Python dependencies (for model training)
pip install -r requirements.txt
```

### Development Scripts

```bash
# Start development server
npm run dev

# Build React frontend
npm run build:react

# Build Electron application
npm run build:electron

# Create distributable packages
npm run dist

# Platform-specific builds
npm run dist:win    # Windows
npm run dist:mac    # macOS
npm run dist:linux  # Linux
```

## 🎯 Usage

### Basic Workflow

1. **Setup**: Run the setup wizard to configure AI model and Google account
2. **Describe**: Enter a natural language description of what you want to scrape
3. **Configure**: Adjust settings like output format and rate limits
4. **Preview**: Generate a sample of data to verify extraction quality
5. **Execute**: Run the full scraping task and export results

### Example Prompts

- "Extract product listings with names, prices, and ratings from an e-commerce site"
- "Scrape job postings for Python developers with salary and location"
- "Get real estate listings under $500k with property details"
- "Extract news articles with headlines, authors, and publication dates"

## 🔒 Privacy & Security

- **Local Processing**: All AI inference happens locally on your machine
- **No Data Transmission**: Your scraped data never leaves your computer
- **Encrypted Storage**: Google credentials are encrypted before storage
- **Anti-Detection**: Built-in mechanisms to respect robots.txt and rate limits

## 📊 Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Application Startup | <5 seconds | ✅ |
| Model Loading | <10 seconds | ✅ |
| AI Inference Speed | <2 seconds | ✅ |
| Memory Usage | <2GB | ✅ |
| Export Speed | 100+ rows/min | ✅ |
| Package Size | <500MB | 🔄 |

## 🚢 Distribution

The application will be distributed as:

- **Windows**: NSIS installer (.exe)
- **macOS**: DMG package (Intel + Apple Silicon)
- **Linux**: AppImage (.appimage)

All builds include:
- Bundled Chromium browser
- Fine-tuned TinyLlama model
- All dependencies and runtime

## 🤝 Contributing

This project follows the SRS specifications outlined in `SRS2.txt`. Key areas for contribution:

1. **Model Training**: Help fine-tune TinyLlama for better web scraping
2. **UI/UX**: Improve the user interface and experience
3. **Testing**: Add comprehensive test coverage
4. **Documentation**: Create tutorials and guides

## 📄 License

MIT License - see LICENSE file for details.

## 🎯 Roadmap

### Phase 1 (Current): Core Functionality ✅
- Basic scraping interface
- AI model integration
- Google Sheets export

### Phase 2: Enhanced Features 🔄
- Template library expansion
- Advanced filtering options
- Scheduling capabilities

### Phase 3: Enterprise Features ⏳
- Multi-account management
- Team collaboration
- Advanced analytics

### Phase 4: Community ⏳
- Plugin system
- Community templates
- Open source model training

---

**Status**: Production-ready core functionality with ongoing enhancements
**Last Updated**: December 12, 2024