# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd vcSource

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp config.env.example .env

# Edit .env with your credentials
# At minimum, add your LinkedIn credentials:
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

### 3. Test the Installation

```bash
# Run the test suite
python test_agent.py
```

### 4. Run Your First Sourcing

```bash
# Basic usage
python main.py --vc-firm "Andreessen Horowitz" --max-results 10

# With specific criteria
python main.py \
  --vc-firm "Sequoia Capital" \
  --stages seed series-a \
  --industries fintech saas \
  --locations "San Francisco" "New York" \
  --max-results 20
```

## 📊 Understanding the Results

The agent provides two key metrics:

### Fit Score (0-100%)
- **Text Similarity**: How well the startup description matches VC's thesis
- **Industry Alignment**: Sector match with VC's focus areas
- **Stage Alignment**: Funding stage compatibility
- **Geographic Alignment**: Location match
- **Network Proximity**: Founder network strength

### Quality Score (0-100%)
- **Founder Quality**: Experience, education, network
- **Company Quality**: Description, industry, location
- **Team Completeness**: Role diversity and coverage

## 🔧 Advanced Usage

### API Mode

```bash
# Start the API server
python api/main.py

# API will be available at http://localhost:8000
# Visit http://localhost:8000/docs for interactive docs
```

### Custom Search

```python
from main import VCSourcingAgent

agent = VCSourcingAgent()
results = agent.source_startups(
    vc_firm="Your VC Firm",
    stages=["pre-seed", "seed"],
    industries=["AI/ML", "Fintech"],
    locations=["San Francisco"],
    keywords=["founder", "startup"],
    max_results=50
)
```

## 🎯 Best Practices

### For LinkedIn Scraping
- Use a dedicated LinkedIn account (not your main one)
- Set reasonable delays between requests (2-5 seconds)
- Don't exceed 100 requests per hour
- Monitor for rate limiting

### For Fit Metrics
- Start with known VC firms (Andreessen Horowitz, Sequoia, etc.)
- Use specific industry keywords
- Focus on early-stage companies (pre-seed to Series A)
- Consider geographic proximity

### For Quality Scoring
- Look for founders with relevant experience
- Prefer teams with diverse roles (CEO, CTO, CPO)
- Consider education and network strength
- Focus on companies in top startup hubs

## 🚨 Important Notes

### Legal & Ethical Considerations
- Always respect LinkedIn's Terms of Service
- Use scraping responsibly and ethically
- Don't overload servers with requests
- Consider the privacy implications

### Rate Limiting
- The agent includes built-in rate limiting
- Adjust `SCRAPING_DELAY` in `.env` if needed
- Monitor logs for rate limit warnings

### Data Quality
- LinkedIn data may be incomplete or outdated
- Always verify important information manually
- Use multiple sources when possible

## 🔍 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
# Make sure you're in the project directory
cd vcSource
# Install dependencies
pip install -r requirements.txt
```

**LinkedIn login issues**
- Check your credentials in `.env`
- Ensure 2FA is disabled or use session cookies
- Try logging in manually first

**Rate limiting**
- Increase `SCRAPING_DELAY` in `.env`
- Reduce `max_results` parameter
- Wait before running again

**Memory issues**
- Reduce `max_results` parameter
- Process results in smaller batches
- Monitor system resources

## 📈 Next Steps

1. **Train Custom Models**: Use your own data to improve fit metrics
2. **Add More Sources**: Integrate Crunchbase, AngelList, etc.
3. **Build Dashboard**: Create a web interface for results
4. **Track Engagement**: Monitor outreach success rates
5. **Expand Analytics**: Add more detailed reporting

## 🆘 Need Help?

- Check the logs in `logs/` directory
- Run `python test_agent.py` to verify setup
- Review the full documentation in `README.md`
- Check the API docs at `http://localhost:8000/docs`

Happy sourcing! 🎉 