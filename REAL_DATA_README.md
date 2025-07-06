# Real Data Implementation Guide

This guide explains how to implement the VC Sourcing Agent with real data instead of mock data.

## 🚀 Quick Start

### 1. Set up Environment

```bash
# Run the setup script
python setup_real_data.py

# Choose option 5 to run all setup steps
```

### 2. Configure API Keys

Edit the `.env` file with your actual API keys:

```env
# Required for real data
USE_MOCK_DATA=false
ENABLE_REAL_SCRAPING=true

# LinkedIn credentials (for company search)
LINKEDIN_EMAIL=your_actual_email@example.com
LINKEDIN_PASSWORD=your_actual_password

# Optional APIs
CRUNCHBASE_API_KEY=your_crunchbase_api_key
OPENAI_API_KEY=your_openai_api_key

# Rate limiting
RATE_LIMIT_DELAY=2
MAX_CONCURRENT_REQUESTS=5
```

### 3. Test Configuration

```bash
# Check environment
python real_data_cli.py check-env

# Test scraper
python real_data_cli.py test-scraper
```

### 4. Run Real Data Sourcing

```bash
# Startup sourcing with real data
python real_data_cli.py startup-sourcing --vc-firm "Sequoia Capital" --max-startups 20

# Talent sourcing
python real_data_cli.py talent-sourcing --vc-firm "Sequoia Capital" --max-talent 10

# Comprehensive analysis
python real_data_cli.py comprehensive --vc-firm "Sequoia Capital" --max-startups 20 --max-talent 10
```

## 📊 Data Sources

### LinkedIn
- **Purpose**: Company search and founder profiles
- **Requirements**: LinkedIn account credentials
- **Rate Limits**: Built-in delays to avoid blocking
- **Data**: Company names, industries, locations, descriptions

### Crunchbase (Optional)
- **Purpose**: Startup funding and company data
- **Requirements**: Crunchbase API key
- **Rate Limits**: API-based limits
- **Data**: Funding stages, company descriptions, industry data

### AngelList/Wellfound
- **Purpose**: Startup discovery and profiles
- **Requirements**: None (public data)
- **Rate Limits**: Built-in delays
- **Data**: Startup profiles, descriptions, locations

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_DATA` | `true` | Set to `false` for real data |
| `ENABLE_REAL_SCRAPING` | `true` | Enable real scraping |
| `RATE_LIMIT_DELAY` | `2` | Seconds between requests |
| `MAX_CONCURRENT_REQUESTS` | `5` | Max concurrent HTTP requests |
| `RAG_CACHE_DURATION` | `3600` | Portfolio cache duration (seconds) |

### Rate Limiting

The system includes built-in rate limiting to avoid being blocked:

- **LinkedIn**: 2-second delays between requests
- **Crunchbase**: API rate limits
- **AngelList**: 2-second delays between requests
- **Portfolio Scraping**: 1-second delays

## 🛠️ Troubleshooting

### Common Issues

#### 1. "No startups found"
- **Cause**: Rate limiting or blocking
- **Solution**: Increase `RATE_LIMIT_DELAY` or use proxy

#### 2. "LinkedIn authentication failed"
- **Cause**: Invalid credentials or 2FA
- **Solution**: Check credentials and disable 2FA temporarily

#### 3. "HTTP 403/429 errors"
- **Cause**: Too many requests
- **Solution**: Increase delays or use proxy rotation

#### 4. "Import errors"
- **Cause**: Missing dependencies
- **Solution**: Run `pip install aiohttp beautifulsoup4 lxml`

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

### Proxy Support

For large-scale scraping, consider using proxies:

```python
# In real_data_scraper.py
proxies = {
    'http': 'http://proxy:port',
    'https': 'https://proxy:port'
}
```

## 📈 Performance Optimization

### 1. Parallel Processing
The system uses async/await for concurrent requests:

```python
# Multiple sources searched in parallel
linkedin_results = await scraper.search_startups_linkedin(keyword, 10)
crunchbase_results = await scraper.search_startups_crunchbase(keyword, 10)
angellist_results = await scraper.search_startups_angel_list(keyword, 10)
```

### 2. Caching
- Portfolio data cached for 1 hour
- Website validation results cached
- Rate limiting prevents duplicate requests

### 3. Batch Processing
- Multiple keywords processed in batches
- Startup analysis done in parallel
- Fit metrics calculated in batches

## 🔒 Security & Compliance

### Data Privacy
- No personal data stored permanently
- API keys stored in environment variables
- Rate limiting prevents abuse

### Terms of Service
- Respect robots.txt files
- Use reasonable delays between requests
- Don't overload servers

### Legal Considerations
- Check terms of service for each platform
- Consider data usage rights
- Respect rate limits and blocking

## 📝 Usage Examples

### Basic Startup Sourcing

```python
from unified_vc_sourcing_agent import UnifiedVCSourcingAgent

async def find_startups():
    agent = UnifiedVCSourcingAgent(use_mock_data=False)
    result = await agent.source_startups_for_vc(
        vc_firm="Sequoia Capital",
        max_startups=20
    )
    return result
```

### Custom Search Keywords

```python
# The system automatically generates keywords, but you can customize:
keywords = ["fintech", "AI", "healthcare", "SaaS"]
# These will be used instead of auto-generated ones
```

### Portfolio Analysis

```python
# The system automatically:
# 1. Scrapes current portfolio companies
# 2. Detects conflicts with existing investments
# 3. Calculates portfolio fit scores
# 4. Provides recommendations
```

## 🎯 Best Practices

### 1. Start Small
- Begin with 5-10 startups per search
- Test with well-known VC firms
- Monitor for errors and blocking

### 2. Use Appropriate Delays
- 2-3 seconds between requests minimum
- Increase delays if you get blocked
- Consider time-of-day for scraping

### 3. Monitor Results
- Check for realistic data
- Verify company information
- Look for patterns in blocking

### 4. Backup Plans
- Keep mock data as fallback
- Have multiple data sources
- Implement graceful degradation

## 🔄 Migration from Mock Data

### Step 1: Test Configuration
```bash
python real_data_cli.py check-env
python real_data_cli.py test-scraper
```

### Step 2: Small Test Run
```bash
python real_data_cli.py startup-sourcing --vc-firm "Sequoia Capital" --max-startups 5
```

### Step 3: Full Implementation
```bash
# Update .env file
USE_MOCK_DATA=false

# Run full analysis
python real_data_cli.py comprehensive --vc-firm "Sequoia Capital"
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Enable debug logging
3. Test with smaller datasets
4. Verify API keys and credentials
5. Check network connectivity

## 🚀 Advanced Features

### Custom Data Sources
You can add new data sources by extending the `RealDataScraper` class:

```python
async def search_startups_custom_source(self, keyword: str, max_count: int):
    # Implement your custom scraping logic
    pass
```

### Enhanced Analysis
With OpenAI API key, you get:
- Better keyword generation
- Enhanced fit analysis
- Improved recommendations

### Database Integration
Store results in database for historical analysis:

```env
DATABASE_URL=sqlite:///vc_sourcing.db
```

This implementation provides a robust, scalable solution for real-time VC sourcing with proper error handling, rate limiting, and compliance considerations. 