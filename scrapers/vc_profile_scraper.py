"""
VC Profile Scraper for getting VC firm information.
"""
import asyncio
from typing import Optional, List
import random

from utils.logger import get_logger
from data.schemas import VCProfile

logger = get_logger(__name__)

class VCProfileScraper:
    """Scraper for VC firm profiles and investment criteria."""
    
    def __init__(self):
        # Mock VC profiles for testing
        self.mock_vc_profiles = {
            "a16z": VCProfile(
                name="Andreessen Horowitz (a16z)",
                investment_thesis="We invest in software companies that are building the future. We focus on early-stage companies with strong technical founders and innovative products.",
                focus_areas=["Software", "AI/ML", "Fintech", "Healthcare", "Enterprise", "Consumer"],
                investment_stages=["Seed", "Series A", "Series B", "Series C"],
                geographic_focus=["San Francisco", "New York", "London", "Tel Aviv"],
                portfolio_companies=["Airbnb", "Coinbase", "GitHub", "Lyft", "Pinterest", "Slack"],
                fund_size="$35B+",
                website="https://a16z.com",
                linkedin_url="https://linkedin.com/company/andreessen-horowitz"
            ),
            "sequoia": VCProfile(
                name="Sequoia Capital",
                investment_thesis="We partner with founders who are building category-defining companies. We look for exceptional teams with breakthrough ideas.",
                focus_areas=["Technology", "Healthcare", "Consumer", "Enterprise", "Fintech"],
                investment_stages=["Seed", "Series A", "Series B", "Series C", "Growth"],
                geographic_focus=["Silicon Valley", "China", "India", "Southeast Asia"],
                portfolio_companies=["Apple", "Google", "WhatsApp", "Zoom", "Stripe", "Airbnb"],
                fund_size="$85B+",
                website="https://sequoiacap.com",
                linkedin_url="https://linkedin.com/company/sequoia-capital"
            ),
            "accel": VCProfile(
                name="Accel",
                investment_thesis="We invest in exceptional founders who are building category-defining companies. We focus on early-stage investments.",
                focus_areas=["SaaS", "Marketplaces", "Fintech", "AI/ML", "Developer Tools"],
                investment_stages=["Seed", "Series A", "Series B"],
                geographic_focus=["San Francisco", "New York", "London", "Bangalore"],
                portfolio_companies=["Facebook", "Slack", "Dropbox", "Spotify", "Atlassian"],
                fund_size="$20B+",
                website="https://accel.com",
                linkedin_url="https://linkedin.com/company/accel"
            ),
            "ycombinator": VCProfile(
                name="Y Combinator",
                investment_thesis="We fund the most promising startups and help them grow. We focus on early-stage companies with strong technical founders.",
                focus_areas=["Software", "AI", "Biotech", "Hardware", "Fintech"],
                investment_stages=["Pre-seed", "Seed"],
                geographic_focus=["San Francisco", "Remote"],
                portfolio_companies=["Airbnb", "Dropbox", "Stripe", "Coinbase", "DoorDash"],
                fund_size="$600M+",
                website="https://ycombinator.com",
                linkedin_url="https://linkedin.com/company/y-combinator"
            ),
            "firstround": VCProfile(
                name="First Round Capital",
                investment_thesis="We help companies build their foundation and scale. We focus on early-stage companies with strong product-market fit.",
                focus_areas=["SaaS", "Marketplaces", "Fintech", "AI/ML", "Developer Tools"],
                investment_stages=["Seed", "Series A"],
                geographic_focus=["San Francisco", "New York", "Philadelphia"],
                portfolio_companies=["Uber", "Square", "Pinterest", "Notion", "Roblox"],
                fund_size="$4B+",
                website="https://firstround.com",
                linkedin_url="https://linkedin.com/company/first-round-capital"
            ),
            "kleiner": VCProfile(
                name="Kleiner Perkins",
                investment_thesis="We partner with entrepreneurs to build the future. We focus on breakthrough technologies and exceptional teams.",
                focus_areas=["Technology", "Healthcare", "Consumer", "Enterprise", "CleanTech"],
                investment_stages=["Seed", "Series A", "Series B", "Series C"],
                geographic_focus=["Silicon Valley", "New York", "Boston"],
                portfolio_companies=["Google", "Amazon", "Genentech", "Spotify", "Uber"],
                fund_size="$12B+",
                website="https://kleinerperkins.com",
                linkedin_url="https://linkedin.com/company/kleiner-perkins"
            ),
            "greylock": VCProfile(
                name="Greylock Partners",
                investment_thesis="We partner with exceptional entrepreneurs to build category-defining companies. We focus on early-stage investments.",
                focus_areas=["Enterprise", "Consumer", "Fintech", "AI/ML", "Security"],
                investment_stages=["Seed", "Series A", "Series B"],
                geographic_focus=["Silicon Valley", "New York", "Boston"],
                portfolio_companies=["LinkedIn", "Facebook", "Airbnb", "Palo Alto Networks", "Workday"],
                fund_size="$15B+",
                website="https://greylock.com",
                linkedin_url="https://linkedin.com/company/greylock-partners"
            ),
            "benchmark": VCProfile(
                name="Benchmark",
                investment_thesis="We partner with entrepreneurs to build great companies. We focus on early-stage companies with exceptional teams.",
                focus_areas=["Consumer", "Enterprise", "Marketplaces", "Fintech", "AI/ML"],
                investment_stages=["Seed", "Series A", "Series B"],
                geographic_focus=["Silicon Valley", "New York"],
                portfolio_companies=["Uber", "Twitter", "Snapchat", "Dropbox", "WeWork"],
                fund_size="$8B+",
                website="https://benchmark.com",
                linkedin_url="https://linkedin.com/company/benchmark-capital"
            ),
            "index": VCProfile(
                name="Index Ventures",
                investment_thesis="We partner with exceptional entrepreneurs building category-defining companies. We focus on early-stage investments.",
                focus_areas=["SaaS", "Fintech", "AI/ML", "Marketplaces", "Developer Tools"],
                investment_stages=["Seed", "Series A", "Series B"],
                geographic_focus=["San Francisco", "London", "New York"],
                portfolio_companies=["Slack", "Dropbox", "Etsy", "Adyen", "Notion"],
                fund_size="$10B+",
                website="https://indexventures.com",
                linkedin_url="https://linkedin.com/company/index-ventures"
            ),
            "foundersfund": VCProfile(
                name="Founders Fund",
                investment_thesis="We invest in companies building things that don't exist yet. We focus on breakthrough technologies and exceptional founders.",
                focus_areas=["Technology", "AI/ML", "Biotech", "Space", "Fintech"],
                investment_stages=["Seed", "Series A", "Series B", "Series C"],
                geographic_focus=["Silicon Valley", "New York", "Los Angeles"],
                portfolio_companies=["Palantir", "SpaceX", "Stripe", "Airbnb", "Lyft"],
                fund_size="$6B+",
                website="https://foundersfund.com",
                linkedin_url="https://linkedin.com/company/founders-fund"
            ),
            "union": VCProfile(
                name="Union Square Ventures",
                investment_thesis="We invest in companies that create value by changing the way people live and work. We focus on early-stage companies.",
                focus_areas=["Fintech", "Marketplaces", "AI/ML", "Consumer", "Enterprise"],
                investment_stages=["Seed", "Series A", "Series B"],
                geographic_focus=["New York", "San Francisco", "London"],
                portfolio_companies=["Twitter", "Etsy", "Coinbase", "Kickstarter", "Duolingo"],
                fund_size="$3B+",
                website="https://usv.com",
                linkedin_url="https://linkedin.com/company/union-square-ventures"
            ),
            "thrive": VCProfile(
                name="Thrive Capital",
                investment_thesis="We partner with entrepreneurs to build category-defining companies. We focus on early-stage investments in technology.",
                focus_areas=["Fintech", "Consumer", "Enterprise", "AI/ML", "Marketplaces"],
                investment_stages=["Seed", "Series A", "Series B"],
                geographic_focus=["New York", "San Francisco", "Los Angeles"],
                portfolio_companies=["Instagram", "Stripe", "GitHub", "Oscar", "Warby Parker"],
                fund_size="$5B+",
                website="https://thrivecap.com",
                linkedin_url="https://linkedin.com/company/thrive-capital"
            ),
            "insight": VCProfile(
                name="Insight Partners",
                investment_thesis="We partner with high-growth software companies to help them scale. We focus on growth-stage investments.",
                focus_areas=["SaaS", "Enterprise", "Fintech", "AI/ML", "Security"],
                investment_stages=["Series B", "Series C", "Growth"],
                geographic_focus=["New York", "San Francisco", "London", "Tel Aviv"],
                portfolio_companies=["Shopify", "Twitter", "Wix", "Qualtrics", "Veeam"],
                fund_size="$30B+",
                website="https://insightpartners.com",
                linkedin_url="https://linkedin.com/company/insight-partners"
            ),
            "tiger": VCProfile(
                name="Tiger Global",
                investment_thesis="We invest in companies that are building the future. We focus on growth-stage companies with strong fundamentals.",
                focus_areas=["Technology", "Fintech", "Consumer", "Enterprise", "AI/ML"],
                investment_stages=["Series B", "Series C", "Growth"],
                geographic_focus=["Global"],
                portfolio_companies=["Stripe", "Coinbase", "Roblox", "Databricks", "Shein"],
                fund_size="$100B+",
                website="https://tigerglobal.com",
                linkedin_url="https://linkedin.com/company/tiger-global-management"
            ),
            "softbank": VCProfile(
                name="SoftBank Vision Fund",
                investment_thesis="We invest in companies that are building the future. We focus on growth-stage companies with breakthrough technologies.",
                focus_areas=["AI/ML", "Robotics", "Fintech", "Consumer", "Enterprise"],
                investment_stages=["Series C", "Growth", "Late Stage"],
                geographic_focus=["Global"],
                portfolio_companies=["Uber", "WeWork", "DoorDash", "ARM", "ByteDance"],
                fund_size="$100B+",
                website="https://softbank.com",
                linkedin_url="https://linkedin.com/company/softbank-group"
            ),
            "nexus": VCProfile(
                name="Nexus Venture Partners",
                investment_thesis="We partner with exceptional entrepreneurs building category-defining companies. We focus on early-stage investments in India and the US.",
                focus_areas=["SaaS", "Fintech", "AI/ML", "Enterprise", "Consumer", "Healthcare"],
                investment_stages=["Seed", "Series A", "Series B"],
                geographic_focus=["India", "United States", "Silicon Valley", "Bangalore", "Mumbai"],
                portfolio_companies=["Postman", "Delhivery", "Snapdeal", "PubMatic", "Kaltura", "Turtlemint"],
                fund_size="$1.5B+",
                website="https://nexusvp.com",
                linkedin_url="https://linkedin.com/company/nexus-venture-partners"
            )
        }
    
    async def scrape_vc_profile(self, vc_firm_name: str) -> Optional[VCProfile]:
        """Scrape VC profile information."""
        logger.info(f"Scraping VC profile for: {vc_firm_name}")
        
        try:
            # Normalize the firm name
            normalized_name = self._normalize_firm_name(vc_firm_name)
            
            # Check if we have a mock profile
            if normalized_name in self.mock_vc_profiles:
                logger.info(f"Found mock profile for {vc_firm_name}")
                return self.mock_vc_profiles[normalized_name]
            
            # If not found, create a generic profile
            logger.info(f"Creating generic profile for {vc_firm_name}")
            return self._create_generic_profile(vc_firm_name)
            
        except Exception as e:
            logger.error(f"Error scraping VC profile for {vc_firm_name}: {e}")
            return None
    
    def _normalize_firm_name(self, firm_name: str) -> str:
        """Normalize firm name for matching."""
        name_lower = firm_name.lower().strip()
        
        # Common variations
        name_mapping = {
            "andreessen horowitz": "a16z",
            "a16z": "a16z",
            "sequoia": "sequoia",
            "sequoia capital": "sequoia",
            "accel": "accel",
            "accel partners": "accel",
            "y combinator": "ycombinator",
            "ycombinator": "ycombinator",
            "first round": "firstround",
            "first round capital": "firstround",
            "kleiner perkins": "kleiner",
            "kleiner": "kleiner",
            "greylock": "greylock",
            "greylock partners": "greylock",
            "benchmark": "benchmark",
            "benchmark capital": "benchmark",
            "index ventures": "index",
            "index": "index",
            "founders fund": "foundersfund",
            "union square ventures": "union",
            "usv": "union",
            "thrive capital": "thrive",
            "thrive": "thrive",
            "insight partners": "insight",
            "insight": "insight",
            "tiger global": "tiger",
            "tiger": "tiger",
            "softbank": "softbank",
            "softbank vision fund": "softbank",
            "nexus": "nexus",
            "nexus venture partners": "nexus"
        }
        
        return name_mapping.get(name_lower, name_lower)
    
    def _create_generic_profile(self, firm_name: str) -> VCProfile:
        """Create a generic VC profile for unknown firms."""
        return VCProfile(
            name=firm_name,
            investment_thesis=f"{firm_name} invests in early-stage companies with strong potential for growth and market disruption.",
            focus_areas=["Technology", "Software", "AI/ML", "Fintech", "Healthcare"],
            investment_stages=["Seed", "Series A", "Series B"],
            geographic_focus=["San Francisco", "New York", "London"],
            portfolio_companies=["Example Company 1", "Example Company 2", "Example Company 3"],
            fund_size="$100M+",
            website=f"https://{firm_name.lower().replace(' ', '')}.com",
            linkedin_url=f"https://linkedin.com/company/{firm_name.lower().replace(' ', '')}"
        )
    
    async def search_vc_firms(self, keywords: List[str]) -> List[VCProfile]:
        """Search for VC firms based on keywords."""
        logger.info(f"Searching for VC firms with keywords: {keywords}")
        
        matching_profiles = []
        
        for keyword in keywords:
            for firm_name, profile in self.mock_vc_profiles.items():
                if (keyword.lower() in firm_name.lower() or 
                    keyword.lower() in profile.focus_areas or
                    keyword.lower() in profile.investment_thesis.lower()):
                    matching_profiles.append(profile)
        
        return list(set(matching_profiles))  # Remove duplicates
    
    def get_all_vc_profiles(self) -> List[VCProfile]:
        """Get all available VC profiles."""
        return list(self.mock_vc_profiles.values())
    
    def add_vc_profile(self, firm_name: str, profile: VCProfile):
        """Add a new VC profile to the database."""
        self.mock_vc_profiles[firm_name.lower()] = profile
        logger.info(f"Added VC profile for {firm_name}") 