# VC Sourcing Agent

An intelligent agent for sourcing early-stage startup talent and calculating fit metrics for VC firms.

## Overview

This agent helps VC firms identify promising early-stage startups (pre-seed, seed, Series A) by:
- Scraping LinkedIn for founder and company data
- Calculating fit metrics based on VC firm profiles and portfolios
- Providing comprehensive company and founder information
- Tracking engagement and success metrics

## Project Structure

```
vc_sourcing_agent/
├── scrapers/              # Data collection modules
│   ├── linkedin_scraper.py
│   ├── vc_profile_scraper.py
│   └── company_scraper.py
├── models/                # ML and scoring models
│   ├── fit_metric.py
│   ├── feature_engineering.py
│   └── training.py
├── metrics/               # Performance tracking
│   ├── engagement_tracker.py
│   ├── quality_scorer.py
│   └── market_analyzer.py
├── data/                  # Data storage and schemas
│   ├── models.py
│   ├── database.py
│   └── schemas.py
├── utils/                 # Utility functions
│   ├── config.py
│   ├── logger.py
│   └── helpers.py
├── api/                   # FastAPI endpoints
│   ├── main.py
│   └── routes.py
├── tests/                 # Test files
├── config/                # Configuration files
├── requirements.txt
└── main.py               # Main orchestration script
```

## Features

### 1. LinkedIn Scraping
- Target early-stage startup founders and employees
- Extract company information, founder backgrounds, and network data
- Handle rate limiting and anti-bot measures

### 2. Fit Metric Calculation
- Text similarity analysis using embeddings
- Portfolio alignment scoring
- Network and geographic proximity metrics
- Machine learning-based fit prediction

### 3. Company Intelligence
- Comprehensive company profiles
- Founder background analysis
- Market positioning and competitive landscape
- Funding stage and traction indicators

### 4. Performance Tracking
- Engagement rate monitoring
- Meeting booking success rates
- Investment conversion tracking
- Quality scoring for founders and companies

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your LinkedIn credentials and API keys
   ```

3. **Run the agent:**
   ```bash
   python main.py --vc-firm "Andreessen Horowitz" --stage "seed"
   ```

## Configuration

Create a `.env` file with:
```
LINKEDIN_EMAIL=your_email
LINKEDIN_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
DATABASE_URL=sqlite:///vc_sourcing.db
```

## Usage Examples

### Basic Sourcing
```python
from vc_sourcing_agent import VCSourcingAgent

agent = VCSourcingAgent()
results = agent.source_startups(
    vc_firm="Sequoia Capital",
    stage="seed",
    industry="fintech",
    location="San Francisco"
)
```

### Fit Analysis
```python
fit_scores = agent.calculate_fit_metrics(
    startups=results,
    vc_profile=vc_profile
)
```

## API Endpoints

- `POST /source` - Source startups for a VC firm
- `GET /fit-metrics` - Calculate fit scores
- `POST /track-engagement` - Track outreach results
- `GET /analytics` - View performance metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details 