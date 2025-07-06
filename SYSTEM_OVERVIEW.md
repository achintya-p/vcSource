# VC Sourcing System Overview

## 🎯 System Purpose

This is a **unified VC sourcing system** that combines:
1. **RAG-based portfolio scraping** - Gets real-time portfolio data from VC firm websites
2. **Startup sourcing** - Finds startups that match VC investment criteria
3. **Talent sourcing** - Finds talent for portfolio companies

## 📁 File Structure

### Core System Files
- `unified_vc_sourcing_agent.py` - **Main unified agent** (use this!)
- `unified_cli.py` - **Simple CLI** for the unified agent
- `portfolio_rag_scraper.py` - RAG system for scraping VC portfolios
- `SYSTEM_OVERVIEW.md` - This documentation

### Legacy Files (Can be removed)
- `live_sourcing_agent.py` - Basic startup sourcing (replaced by unified agent)
- `dynamic_sourcing_agent.py` - Enhanced startup sourcing (replaced by unified agent)
- `talent_sourcing_agent.py` - Standalone talent sourcing (replaced by unified agent)
- `vc_talent_sourcing_cli.py` - Complex CLI (replaced by unified_cli.py)

## 🚀 How to Use

### Quick Start
```bash
# Comprehensive analysis (startups + talent)
python unified_cli.py "Nexus Venture Partners"

# Just startup sourcing
python unified_cli.py "Nexus Venture Partners" --mode startups

# Just talent sourcing
python unified_cli.py "Nexus Venture Partners" --mode talent

# Save results to file
python unified_cli.py "Nexus Venture Partners" --output results.json
```

### Programmatic Usage
```python
from unified_vc_sourcing_agent import UnifiedVCSourcingAgent

agent = UnifiedVCSourcingAgent(use_mock_data=True)

# Startup sourcing
startup_results = await agent.source_startups_for_vc("Nexus Venture Partners")

# Talent sourcing
talent_results = await agent.source_talent_for_portfolio("Nexus Venture Partners")

# Comprehensive analysis
comprehensive_results = await agent.comprehensive_vc_analysis("Nexus Venture Partners")
```

## 🔧 System Components

### 1. RAG Portfolio Scraper (`portfolio_rag_scraper.py`)
- **Purpose**: Scrapes real-time portfolio data from VC firm websites
- **Features**:
  - Pattern-based scraping for major VC firms
  - Fallback to static data when scraping fails
  - Filters out job listings and irrelevant content
  - Caches results for performance

### 2. Unified VC Sourcing Agent (`unified_vc_sourcing_agent.py`)
- **Purpose**: Main agent that combines all functionality
- **Features**:
  - **Startup Sourcing**: Finds startups matching VC criteria
  - **Talent Sourcing**: Finds talent for portfolio companies
  - **Portfolio Analysis**: Analyzes conflicts and fit
  - **Comprehensive Analysis**: Runs both sourcing types

### 3. Supporting Components
- `scrapers/linkedin_scraper.py` - LinkedIn data extraction
- `scrapers/vc_profile_scraper.py` - VC profile data
- `models/optimized_fit_metric.py` - Fit calculation algorithms
- `metrics/quality_scorer.py` - Quality scoring
- `data/schemas.py` - Data structures

## 📊 Output Format

### Startup Sourcing Results
```json
{
  "vc_firm": "Nexus Venture Partners",
  "analysis_type": "startup_sourcing",
  "portfolio_companies": ["Snapdeal", "Delhivery", ...],
  "results": [
    {
      "startup_name": "AI Solutions 1",
      "industry": "AI/ML",
      "overall_score": 85.2,
      "fit_score": 82.1,
      "quality_score": 78.5,
      "portfolio_fit_score": 75.0,
      "recommendation": "Strong Match - Highly recommend",
      "pros": ["Excellent fit with VC criteria", "High quality founders"],
      "cons": ["Moderate portfolio conflicts"]
    }
  ]
}
```

### Talent Sourcing Results
```json
{
  "vc_firm": "Nexus Venture Partners",
  "analysis_type": "talent_sourcing",
  "portfolio_companies": ["Snapdeal", "Delhivery", ...],
  "results": [
    {
      "name": "Alex Johnson",
      "title": "CEO",
      "company": "Snapdeal",
      "platform": "linkedin",
      "match_score": 75.0,
      "pros": ["Senior leadership experience", "Large professional network"],
      "cons": ["Limited experience details"]
    }
  ]
}
```

## 🎯 Use Cases

### 1. VC Investment Research
- Find startups that match investment criteria
- Analyze portfolio conflicts
- Assess market fit and quality

### 2. Portfolio Company Support
- Find talent for portfolio companies
- Identify hiring opportunities
- Assess talent market

### 3. Market Intelligence
- Understand VC investment patterns
- Track portfolio company growth
- Identify emerging trends

## 🔄 Data Flow

```
1. Input VC Firm Name
   ↓
2. RAG Scraper → Portfolio Companies
   ↓
3. Startup Sourcing → Find Matching Startups
   ↓
4. Talent Sourcing → Find Talent for Portfolio
   ↓
5. Analysis → Calculate Scores & Recommendations
   ↓
6. Output → Structured Results with Pros/Cons
```

## 🛠️ Configuration

### Environment Variables
- `USE_MOCK_DATA=true` - Use mock data instead of real scraping
- `LINKEDIN_EMAIL` - LinkedIn login email
- `LINKEDIN_PASSWORD` - LinkedIn login password

### Mock Data Mode
- Set `use_mock_data=True` for testing without real API calls
- Provides realistic sample data for all components
- Perfect for development and testing

## 🚀 Performance

### Current Performance (Mock Data)
- **Startup Sourcing**: ~2-5 seconds for 20 startups
- **Talent Sourcing**: ~1-3 seconds for 50 talent profiles
- **Comprehensive Analysis**: ~5-10 seconds total

### Real Data Performance
- **RAG Scraping**: 10-30 seconds per VC firm (with rate limiting)
- **LinkedIn Scraping**: 5-15 seconds per search (with rate limiting)
- **Total Analysis**: 30-60 seconds for comprehensive analysis

## 🔧 Future Enhancements

### Planned Features
1. **Real-time Crunchbase API** integration
2. **Twitter API** integration for talent sourcing
3. **Advanced NLP** for better matching
4. **Database storage** for historical data
5. **Web dashboard** for visualization
6. **Email alerts** for new matches

### Scalability Improvements
1. **Parallel processing** for multiple VC firms
2. **Distributed scraping** for better performance
3. **Caching layer** for frequently accessed data
4. **API rate limiting** optimization

## 📝 Migration Guide

### From Legacy Agents
If you were using the old agents:

1. **Replace** `live_sourcing_agent.py` → `unified_vc_sourcing_agent.py`
2. **Replace** `dynamic_sourcing_agent.py` → `unified_vc_sourcing_agent.py`
3. **Replace** `talent_sourcing_agent.py` → `unified_vc_sourcing_agent.py`

### Code Migration
```python
# Old way
from live_sourcing_agent import LiveSourcingAgent
agent = LiveSourcingAgent()
results = await agent.source_startups(vc_firm)

# New way
from unified_vc_sourcing_agent import UnifiedVCSourcingAgent
agent = UnifiedVCSourcingAgent()
results = await agent.source_startups_for_vc(vc_firm)
```

## 🎉 Summary

The **Unified VC Sourcing Agent** is now the single point of entry for all VC sourcing needs. It provides:

- ✅ **Clean, unified interface**
- ✅ **RAG-based portfolio scraping**
- ✅ **Startup sourcing with detailed analysis**
- ✅ **Talent sourcing for portfolio companies**
- ✅ **Comprehensive reporting with pros/cons**
- ✅ **Easy CLI and programmatic access**

Use `unified_cli.py` for quick analysis or `unified_vc_sourcing_agent.py` for programmatic integration! 