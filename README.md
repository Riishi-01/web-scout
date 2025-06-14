# Intelligent Web Scraping Agent (IWSA)

An AI-powered web scraping system that analyzes user prompts, performs website reconnaissance, uses LLM intelligence to generate optimal scraping strategies, and exports structured data to Google Sheets.

## 🌟 Features

- **Natural Language Processing**: Describe what you want to scrape in plain English
- **AI-Powered Strategy Generation**: LLM intelligence generates optimal scraping approaches
- **Automatic Website Analysis**: Reconnaissance engine analyzes site structure and anti-bot measures
- **Dynamic Selector Generation**: AI creates and adapts CSS selectors on the fly
- **Anti-Detection Mechanisms**: Sophisticated evasion techniques including proxy rotation and behavioral simulation
- **Multiple Export Formats**: Google Sheets, CSV, JSON, Excel
- **Free Tier Optimized**: Designed to work within GitHub Actions and other free infrastructure
- **Error Recovery**: LLM-powered error analysis and resolution

## 🏗️ Architecture

```
User Prompt → Reconnaissance Engine → LLM Analysis → Dynamic Scraper → Data Export
```

### Core Components

- **Prompt Processing Layer**: Natural language understanding and intent extraction
- **Reconnaissance Engine**: Website structure discovery and analysis
- **LLM Intelligence Hub**: Multi-provider AI coordination (OpenAI/Claude/HuggingFace)
- **Dynamic Scraper Core**: Playwright-based scraping with anti-detection
- **Data Pipeline**: Processing, validation, and export

## 🚀 Quick Start

### GitHub Actions (Recommended)

1. Fork this repository
2. Add your API keys to repository secrets:
   - `MONGODB_URI`: MongoDB connection string
   - `GOOGLE_CREDENTIALS`: Base64-encoded Google service account JSON
3. Go to Actions → "Intelligent Web Scraping Agent"
4. Click "Run workflow" and enter your scraping prompt

### Local Installation

```bash
# Clone repository
git clone <repository-url>
cd Crawler_max

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env

# Run the scraper
python main.py "Scrape job listings from example-jobs.com for Python developers"
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or run directly
docker build -t iwsa .
docker run -e PROMPT="Your scraping request" iwsa
```

## 📝 Usage Examples

### Basic Usage

```bash
python main.py "Scrape product listings from electronics store showing name, price, and rating"
```

### Advanced Usage with Environment Variables

```bash
export PROMPT="Extract job postings from tech-jobs.com in San Francisco with salary > 100k"
export SCRAPING_PROFILE="conservative"
export EXPORT_FORMAT="sheets"
export MAX_PAGES="50"
python main.py
```

### GitHub Actions Workflow

```yaml
- name: Run IWSA
  uses: ./.github/workflows/scraping.yml
  with:
    prompt: "Scrape real estate listings under $500k"
    llm_provider: "openai"
    scraping_profile: "balanced"
    export_format: "sheets"
```

## ⚙️ Configuration

### Environment Variables

```env
# LLM Configuration
OPENAI_API_KEY=sk-your-openai-key
CLAUDE_API_KEY=your-claude-key
PRIMARY_LLM_PROVIDER=openai

# Storage
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/iwsa
GOOGLE_CREDENTIALS=base64_encoded_service_account_json

# Scraping
MAX_CONCURRENT_BROWSERS=3
DEFAULT_TIMEOUT=30
RATE_LIMIT_DELAY=2
```

### Scraping Profiles

- **Conservative**: Slow, respectful, maximum anti-detection (5s delays)
- **Balanced**: Moderate speed with good anti-detection (2s delays)  
- **Aggressive**: Fast scraping with minimal anti-detection (1s delays)
- **Stealth**: Maximum evasion with residential proxies (8s delays)

## 🧠 LLM Provider Setup

### OpenAI

1. Get API key from [OpenAI Platform](https://platform.openai.com)
2. Set `OPENAI_API_KEY` environment variable
3. Recommended models: `gpt-4`, `gpt-3.5-turbo`

### Claude (Anthropic)

1. Get API key from [Anthropic Console](https://console.anthropic.com)
2. Set `CLAUDE_API_KEY` environment variable  
3. Recommended models: `claude-3-sonnet`, `claude-3-haiku`

### HuggingFace (Free Fallback)

1. Get token from [HuggingFace](https://huggingface.co/settings/tokens)
2. Set `HF_API_KEY` environment variable
3. Free tier with rate limits

## 📊 Data Export

### Google Sheets

1. Create Google Cloud Project
2. Enable Google Sheets API
3. Create Service Account and download JSON
4. Encode JSON as base64 and set `GOOGLE_CREDENTIALS`
5. Share target spreadsheet with service account email

### Other Formats

- **CSV**: Comma-separated values
- **JSON**: Structured JSON with metadata
- **Excel**: XLSX with formatting

## 🔧 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v --cov=iwsa

# Run specific test
pytest tests/test_prompt_processor.py -v
```

### Code Quality

```bash
# Format code
black iwsa/
isort iwsa/

# Lint code  
flake8 iwsa/
pylint iwsa/

# Type checking
mypy iwsa/
```

### Adding New Exporters

```python
from iwsa.data.exporters import BaseExporter

class CustomExporter(BaseExporter):
    async def export(self, data, metadata=None):
        # Implementation
        pass
```

## 📈 Monitoring & Performance

### System Health Check

```bash
python -c "
import asyncio
from iwsa.core.engine import ScrapingEngine
from iwsa.config import Settings

async def health_check():
    engine = ScrapingEngine(Settings())
    health = await engine.health_check()
    print(health)

asyncio.run(health_check())
"
```

### Performance Tuning

- Adjust `MAX_CONCURRENT_BROWSERS` based on available memory
- Use appropriate scraping profile for site type
- Monitor rate limiting and adjust delays
- Use proxy rotation for high-volume scraping

## 🛡️ Legal & Ethical Guidelines

- **Respect robots.txt**: Check site policies before scraping
- **Rate Limiting**: Don't overwhelm servers with requests
- **Public Data Only**: Only scrape publicly accessible information
- **Terms of Service**: Review and comply with site ToS
- **Data Privacy**: Don't scrape personal/private information

## 🔒 Security

- API keys are never logged or stored
- Browser fingerprints are randomized
- Proxy rotation prevents IP blocking
- Minimal data retention policies
- Encrypted transmission of sensitive data

## 🐛 Troubleshooting

### Common Issues

**"No LLM provider configured"**
```bash
# Ensure API key is set
export OPENAI_API_KEY=your-key-here
```

**"MongoDB connection failed"**
```bash
# Check connection string
export MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/db
```

**"Google Sheets authentication failed"**
```bash
# Verify credentials are base64 encoded
echo $GOOGLE_CREDENTIALS | base64 -d | jq .
```

**"Rate limited by site"**
- Switch to conservative profile
- Add proxy rotation
- Increase delays between requests

### Debug Mode

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python main.py "your prompt"
```

## 📚 API Reference

### Core Classes

```python
from iwsa import ScrapingEngine, Settings

# Initialize
settings = Settings()
engine = ScrapingEngine(settings)

# Process request
response = await engine.process_request("Scrape products from store.com")

# Check results
if response.success:
    print(f"Extracted {response.total_records} records")
    print(f"Export URL: {response.export_url}")
```

### Configuration

```python
from iwsa.config import Settings, ScrapingProfiles

# Load settings
settings = Settings()

# Get scraping profile
profile = ScrapingProfiles.get_profile("conservative")

# Custom profile
custom = ScrapingProfiles.create_custom_profile(
    "balanced", 
    {"rate_limit": 3.0}
)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/iwsa.git
cd iwsa

# Install in development mode
pip install -e .

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for browser automation
- [OpenAI](https://openai.com/) and [Anthropic](https://anthropic.com/) for LLM APIs
- [MongoDB](https://mongodb.com/) for data storage
- [Google Sheets API](https://developers.google.com/sheets/api) for data export

## 📞 Support

- 📧 Email: support@iwsa.dev
- 🐛 Issues: [GitHub Issues](https://github.com/repo/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/repo/discussions)
- 📖 Docs: [Full Documentation](https://iwsa.dev/docs)

---

**⚠️ Disclaimer**: This tool is for educational and legitimate research purposes. Users are responsible for complying with applicable laws, website terms of service, and ethical scraping practices.