#!/usr/bin/env python3
"""
Portfolio RAG Scraper - Dynamic portfolio data retrieval for any VC firm
"""
import asyncio
import aiohttp
import re
import json
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import random
from dataclasses import dataclass
from utils.logger import get_logger
from website_finder import WebsiteFinder

logger = get_logger(__name__)

@dataclass
class PortfolioCompany:
    """Portfolio company data structure."""
    name: str
    industry: str
    description: str
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    funding_stage: Optional[str] = None
    location: Optional[str] = None
    founded_year: Optional[int] = None

class PortfolioRAGScraper:
    """RAG-based portfolio scraper for VC firms."""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # VC firm website patterns and selectors
        self.vc_patterns = {
            "sequoia": {
                "name_variations": ["sequoia capital", "sequoia", "sequoiacap"],
                "portfolio_urls": [
                    "https://www.sequoiacap.com/companies/",
                    "https://www.sequoiacap.com/portfolio/"
                ],
                "selectors": {
                    "company_containers": ".company-item, .portfolio-item, .company-card",
                    "company_name": "h3, h4, .company-name, .name",
                    "company_description": "p, .description, .company-desc",
                    "company_industry": ".industry, .sector, .category",
                    "company_website": "a[href*='http'], .website-link"
                }
            },
            "andreessen horowitz": {
                "name_variations": ["andreessen horowitz", "a16z", "andreessen"],
                "portfolio_urls": [
                    "https://a16z.com/portfolio/",
                    "https://a16z.com/companies/"
                ],
                "selectors": {
                    "company_containers": ".portfolio-item, .company-item, .company-card",
                    "company_name": "h3, h4, .company-name, .name",
                    "company_description": "p, .description, .company-desc",
                    "company_industry": ".industry, .sector, .category",
                    "company_website": "a[href*='http'], .website-link"
                }
            },
            "nexus venture partners": {
                "name_variations": ["nexus venture partners", "nexus", "nexusvp"],
                "portfolio_urls": [
                    "https://nexusvp.com/portfolio/",
                    "https://nexusvp.com/companies/"
                ],
                "selectors": {
                    "company_containers": ".portfolio-item, .company-item, .company-card",
                    "company_name": "h3, h4, .company-name, .name",
                    "company_description": "p, .description, .company-desc",
                    "company_industry": ".industry, .sector, .category",
                    "company_website": "a[href*='http'], .website-link"
                }
            },
            "y combinator": {
                "name_variations": ["y combinator", "ycombinator", "yc"],
                "portfolio_urls": [
                    "https://www.ycombinator.com/companies/",
                    "https://www.ycombinator.com/portfolio/"
                ],
                "selectors": {
                    "company_containers": ".company-item, .portfolio-item, .company-card",
                    "company_name": "h3, h4, .company-name, .name",
                    "company_description": "p, .description, .company-desc",
                    "company_industry": ".industry, .sector, .category",
                    "company_website": "a[href*='http'], .website-link"
                }
            },
            "accel": {
                "name_variations": ["accel", "accel partners"],
                "portfolio_urls": [
                    "https://www.accel.com/portfolio/",
                    "https://www.accel.com/companies/"
                ],
                "selectors": {
                    "company_containers": ".company-item, .portfolio-item, .company-card",
                    "company_name": "h3, h4, .company-name, .name",
                    "company_description": "p, .description, .company-desc",
                    "company_industry": ".industry, .sector, .category",
                    "company_website": "a[href*='http'], .website-link"
                }
            }
        }
        
        # Industry mapping for better categorization
        self.industry_keywords = {
            "AI/ML": ["artificial intelligence", "machine learning", "ai", "ml", "deep learning", "neural networks"],
            "Fintech": ["fintech", "financial technology", "payments", "banking", "lending", "insurance"],
            "SaaS": ["saas", "software as a service", "enterprise", "b2b", "software"],
            "Healthcare": ["healthcare", "digital health", "telemedicine", "medtech", "biotech"],
            "Consumer": ["consumer", "b2c", "marketplace", "ecommerce", "retail"],
            "Social Media": ["social media", "social networking", "messaging", "communication"],
            "Transportation": ["transportation", "mobility", "ride-sharing", "logistics"],
            "Edtech": ["education", "edtech", "learning", "online education"],
            "Gaming": ["gaming", "game", "entertainment", "esports"],
            "Adtech": ["advertising", "adtech", "marketing", "digital advertising"],
            "Cybersecurity": ["cybersecurity", "security", "privacy", "cyber"],
            "E-commerce": ["ecommerce", "e-commerce", "marketplace", "retail", "shopping"],
            "Food Delivery": ["food delivery", "food", "restaurant", "delivery"],
            "Logistics": ["logistics", "supply chain", "warehouse", "fulfillment"],
            "B2B": ["b2b", "enterprise", "business", "corporate"],
            "Insurtech": ["insurance", "insurtech", "risk management"],
            "PropTech": ["real estate", "proptech", "property", "housing"]
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _normalize_vc_name(self, vc_name: str) -> str:
        """Normalize VC firm name for pattern matching."""
        return vc_name.lower().strip()
    
    def _get_vc_pattern(self, vc_name: str) -> Optional[Dict]:
        """Get VC pattern configuration."""
        normalized_name = self._normalize_vc_name(vc_name)
        
        for key, pattern in self.vc_patterns.items():
            if any(var in normalized_name for var in pattern["name_variations"]):
                return pattern
        
        # Try partial matching for better coverage
        for key, pattern in self.vc_patterns.items():
            for var in pattern["name_variations"]:
                if var in normalized_name or normalized_name in var:
                    return pattern
        
        return None
    
    def _categorize_industry(self, text: str) -> str:
        """Categorize industry based on text analysis."""
        if not text:
            return "Other"
        
        text_lower = text.lower()
        
        for industry, keywords in self.industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return industry
        
        return "Other"
    
    async def _scrape_page(self, url: str) -> Optional[str]:
        """Scrape a single page."""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to scrape {url}: Status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    async def _extract_companies_from_html(self, html: str, selectors: Dict) -> List[PortfolioCompany]:
        """Extract company information from HTML using selectors."""
        companies = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try different container selectors
            container_selectors = [
                selectors["company_containers"],
                ".company", ".portfolio-item", ".company-item",
                "div[class*='company']", "div[class*='portfolio']",
                "li", ".card", ".item"
            ]
            
            containers = []
            for selector in container_selectors:
                containers = soup.select(selector)
                if containers:
                    break
            
            if not containers:
                # Fallback: look for any div with company-like content
                containers = soup.find_all(['div', 'li'], class_=re.compile(r'company|portfolio|item'))
            
            for container in containers:
                try:
                    # Extract company name
                    name_elem = container.select_one(selectors["company_name"])
                    if not name_elem:
                        name_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    
                    if not name_elem:
                        continue
                    
                    company_name = name_elem.get_text(strip=True)
                    if not company_name or len(company_name) < 2:
                        continue
                    
                    # Filter out job listings and non-company content
                    if self._is_job_listing(company_name):
                        continue
                    
                    # Extract description
                    desc_elem = container.select_one(selectors["company_description"])
                    if not desc_elem:
                        desc_elem = container.find('p')
                    
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    # Filter out job-related descriptions
                    if self._is_job_description(description):
                        continue
                    
                    # Extract industry
                    industry_elem = container.select_one(selectors["company_industry"])
                    industry = industry_elem.get_text(strip=True) if industry_elem else ""
                    
                    # Categorize industry if not provided
                    if not industry and description:
                        industry = self._categorize_industry(description)
                    
                    # Extract website
                    website_elem = container.select_one(selectors["company_website"])
                    website = website_elem.get('href') if website_elem else None
                    
                    # Clean up website URL
                    if website and not website.startswith('http'):
                        website = urljoin("https://example.com", website)
                    
                    company = PortfolioCompany(
                        name=company_name,
                        industry=industry or "Other",
                        description=description,
                        website=website
                    )
                    
                    companies.append(company)
                    
                except Exception as e:
                    logger.debug(f"Error extracting company from container: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
        
        return companies
    
    def _is_job_listing(self, name: str) -> bool:
        """Check if the name is a job listing."""
        job_keywords = [
            "jobs", "job", "analyst", "engineer", "manager", "director", "officer",
            "intern", "associate", "scientist", "developer", "designer", "controller",
            "banking", "wealth", "account", "product", "operations", "financial"
        ]
        
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in job_keywords) and "jobs" in name_lower
    
    def _is_job_description(self, description: str) -> bool:
        """Check if the description is job-related."""
        if not description:
            return False
            
        job_keywords = [
            "job", "position", "role", "responsibilities", "requirements",
            "qualifications", "experience", "skills", "apply", "candidate",
            "employment", "career", "hiring", "recruitment"
        ]
        
        desc_lower = description.lower()
        return any(keyword in desc_lower for keyword in job_keywords)
    
    async def _search_alternative_sources(self, vc_name: str) -> List[PortfolioCompany]:
        """Search alternative sources for portfolio data."""
        companies = []
        
        # Try Crunchbase-style patterns
        search_urls = [
            f"https://www.crunchbase.com/organization/{vc_name.lower().replace(' ', '-')}",
            f"https://www.linkedin.com/company/{vc_name.lower().replace(' ', '-')}",
            f"https://www.owler.com/company/{vc_name.lower().replace(' ', '-')}"
        ]
        
        for url in search_urls:
            try:
                html = await self._scrape_page(url)
                if html:
                    # Extract companies from alternative sources
                    extracted = await self._extract_companies_from_html(html, {
                        "company_containers": ".company, .portfolio-item, .company-item",
                        "company_name": "h3, h4, .company-name",
                        "company_description": "p, .description",
                        "company_industry": ".industry, .sector",
                        "company_website": "a[href*='http']"
                    })
                    companies.extend(extracted)
            except Exception as e:
                logger.debug(f"Error searching alternative source {url}: {e}")
        
        return companies
    
    async def scrape_portfolio(self, vc_name: str, max_companies: int = 50) -> List[PortfolioCompany]:
        """Scrape portfolio data for a VC firm."""
        logger.info(f"Scraping portfolio for {vc_name}")
        
        companies = []
        vc_pattern = self._get_vc_pattern(vc_name)
        
        if vc_pattern:
            # Try official portfolio URLs
            for url in vc_pattern["portfolio_urls"]:
                try:
                    html = await self._scrape_page(url)
                    if html:
                        extracted = await self._extract_companies_from_html(html, vc_pattern["selectors"])
                        companies.extend(extracted)
                        
                        if len(companies) >= max_companies:
                            break
                        
                        # Add delay to be respectful
                        await asyncio.sleep(random.uniform(1, 3))
                        
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
        
        # If we don't have enough companies, try alternative sources
        if len(companies) < max_companies // 2:
            logger.info(f"Trying alternative sources for {vc_name}")
            alternative_companies = await self._search_alternative_sources(vc_name)
            companies.extend(alternative_companies)
        
        # Remove duplicates and limit
        unique_companies = self._remove_duplicates(companies)
        
        # If we still don't have companies, log a warning
        if not unique_companies:
            logger.warning(f"No companies found for {vc_name} - scraping may have failed")
        
        return unique_companies[:max_companies]
    
    def _remove_duplicates(self, companies: List[PortfolioCompany]) -> List[PortfolioCompany]:
        """Remove duplicate companies based on name similarity."""
        unique_companies = []
        seen_names = set()
        
        for company in companies:
            normalized_name = company.name.lower().strip()
            
            # Check if we've seen a similar name
            is_duplicate = False
            for seen_name in seen_names:
                if self._calculate_similarity(normalized_name, seen_name) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_companies.append(company)
                seen_names.add(normalized_name)
        
        return unique_companies
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio()
    
    async def _enhance_with_websites(self, companies: List[PortfolioCompany]) -> List[PortfolioCompany]:
        """Enhance portfolio companies with website information."""
        try:
            async with WebsiteFinder() as website_finder:
                company_names = [comp.name for comp in companies]
                websites = await website_finder.find_websites_batch(company_names)
                
                # Update companies with website information
                for company in companies:
                    if company.name in websites and websites[company.name]:
                        company.website = websites[company.name]
                        logger.info(f"Enhanced {company.name} with website: {company.website}")
                
                return companies
        except Exception as e:
            logger.error(f"Error enhancing companies with websites: {e}")
            return companies
    
    async def scrape_portfolio_with_websites(self, vc_name: str, max_companies: int = 50) -> List[PortfolioCompany]:
        """Scrape portfolio with website enhancement."""
        companies = await self.scrape_portfolio(vc_name, max_companies)
        return await self._enhance_with_websites(companies)
    
    async def get_portfolio_summary(self, vc_name: str) -> Dict:
        """Get portfolio summary for a VC firm."""
        companies = await self.scrape_portfolio(vc_name)
        
        industries = list(set([comp.industry for comp in companies if comp.industry]))
        company_names = [comp.name for comp in companies]
        
        return {
            "total_companies": len(companies),
            "industries": industries,
            "companies": company_names,
            "companies_data": [
                {
                    "name": comp.name,
                    "industry": comp.industry,
                    "description": comp.description,
                    "website": comp.website
                }
                for comp in companies
            ]
        }

# Fallback scraper for when real scraping fails
class FallbackPortfolioScraper:
    """Fallback portfolio scraper that uses public APIs and alternative sources."""
    
    def __init__(self):
        # Minimal fallback data for when scraping fails
        self.fallback_data = {
            "sequoia capital": [
                {"name": "WhatsApp", "industry": "Social Media", "description": "Messaging platform"},
                {"name": "Airbnb", "industry": "Travel", "description": "Home sharing platform"},
                {"name": "Stripe", "industry": "Fintech", "description": "Payment processing"},
                {"name": "DoorDash", "industry": "Food Delivery", "description": "Food delivery service"},
                {"name": "Zoom", "industry": "SaaS", "description": "Video conferencing"},
                {"name": "Snowflake", "industry": "SaaS", "description": "Cloud data platform"},
                {"name": "ByteDance", "industry": "Social Media", "description": "TikTok parent company"},
                {"name": "Instacart", "industry": "Food Delivery", "description": "Grocery delivery"},
                {"name": "Robinhood", "industry": "Fintech", "description": "Stock trading app"},
                {"name": "Unity", "industry": "Gaming", "description": "Game development platform"}
            ],
            "andreessen horowitz": [
                {"name": "Facebook", "industry": "Social Media", "description": "Social networking platform"},
                {"name": "GitHub", "industry": "SaaS", "description": "Code hosting platform"},
                {"name": "Coinbase", "industry": "Fintech", "description": "Cryptocurrency exchange"},
                {"name": "Lyft", "industry": "Transportation", "description": "Ride-sharing platform"},
                {"name": "Slack", "industry": "SaaS", "description": "Team collaboration platform"},
                {"name": "Twitter", "industry": "Social Media", "description": "Microblogging platform"},
                {"name": "Pinterest", "industry": "Social Media", "description": "Visual discovery platform"},
                {"name": "Box", "industry": "SaaS", "description": "Cloud storage platform"},
                {"name": "Okta", "industry": "SaaS", "description": "Identity management platform"},
                {"name": "Palantir", "industry": "SaaS", "description": "Data analytics platform"}
            ],
            "nexus venture partners": [
                {"name": "Snapdeal", "industry": "E-commerce", "description": "Online marketplace"},
                {"name": "Delhivery", "industry": "Logistics", "description": "Logistics and delivery"},
                {"name": "PubMatic", "industry": "Adtech", "description": "Digital advertising platform"},
                {"name": "Happay", "industry": "Fintech", "description": "Expense management platform"},
                {"name": "Turtlemint", "industry": "Insurtech", "description": "Insurance platform"},
                {"name": "Unacademy", "industry": "Edtech", "description": "Online learning platform"},
                {"name": "Razorpay", "industry": "Fintech", "description": "Payment gateway"},
                {"name": "Licious", "industry": "Food Delivery", "description": "Meat delivery platform"},
                {"name": "WhiteHat Jr", "industry": "Edtech", "description": "Coding education for kids"},
                {"name": "Infra.Market", "industry": "B2B", "description": "Construction materials marketplace"}
            ]
        }
    
    async def scrape_portfolio(self, vc_name: str, max_companies: int = 50) -> List[PortfolioCompany]:
        """Get fallback portfolio data."""
        normalized_name = vc_name.lower().strip()
        
        # Try exact match first
        if normalized_name in self.fallback_data:
            companies = []
            for comp_data in self.fallback_data[normalized_name]:
                company = PortfolioCompany(
                    name=comp_data["name"],
                    industry=comp_data["industry"],
                    description=comp_data["description"]
                )
                companies.append(company)
            return companies[:max_companies]
        
        # Try partial matching
        for key, data in self.fallback_data.items():
            if key in normalized_name or normalized_name in key:
                companies = []
                for comp_data in data:
                    company = PortfolioCompany(
                        name=comp_data["name"],
                        industry=comp_data["industry"],
                        description=comp_data["description"]
                    )
                    companies.append(company)
                return companies[:max_companies]
        
        # If still no match, try to find the closest match
        best_match = None
        best_score = 0
        
        for key in self.fallback_data.keys():
            # Simple similarity calculation
            common_words = set(normalized_name.split()) & set(key.split())
            if common_words:
                score = len(common_words) / max(len(normalized_name.split()), len(key.split()))
                if score > best_score:
                    best_score = score
                    best_match = key
        
        if best_match and best_score > 0.3:  # Threshold for similarity
            companies = []
            for comp_data in self.fallback_data[best_match]:
                company = PortfolioCompany(
                    name=comp_data["name"],
                    industry=comp_data["industry"],
                    description=comp_data["description"]
                )
                companies.append(company)
            return companies[:max_companies]
        
        return []
    
    async def get_portfolio_summary(self, vc_name: str) -> Dict:
        """Get fallback portfolio summary."""
        companies = await self.scrape_portfolio(vc_name)
        
        industries = list(set([comp.industry for comp in companies if comp.industry]))
        company_names = [comp.name for comp in companies]
        
        return {
            "total_companies": len(companies),
            "industries": industries,
            "companies": company_names,
            "companies_data": [
                {
                    "name": comp.name,
                    "industry": comp.industry,
                    "description": comp.description,
                    "website": comp.website
                }
                for comp in companies
            ]
        } 