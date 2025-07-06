#!/usr/bin/env python3
"""
Website Finder Utility
Discovers and validates company landing pages from various sources
"""
import asyncio
import aiohttp
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import dns.resolver
import socket
from bs4 import BeautifulSoup

from utils.logger import logger

class WebsiteFinder:
    """Utility to find and validate company websites."""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Common domain patterns for companies
        self.domain_patterns = [
            "{company}.com",
            "{company}.io",
            "{company}.co",
            "{company}.ai",
            "{company}.tech",
            "{company}.app",
            "{company}.org",
            "www.{company}.com",
            "www.{company}.io",
            "www.{company}.co",
            "www.{company}.ai",
            "www.{company}.tech",
            "www.{company}.app",
            "www.{company}.org"
        ]
        
        # Common TLDs for tech companies
        self.tech_tlds = ['.com', '.io', '.co', '.ai', '.tech', '.app', '.org', '.net']
        
        # Search engines for finding websites
        self.search_urls = [
            "https://www.google.com/search?q={company}+official+website",
            "https://www.bing.com/search?q={company}+official+website",
            "https://duckduckgo.com/?q={company}+official+website"
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for domain generation."""
        # Remove common suffixes
        name = company_name.lower()
        suffixes = [' inc', ' llc', ' ltd', ' corp', ' corporation', ' company', ' co']
        for suffix in suffixes:
            name = name.replace(suffix, '')
        
        # Remove special characters and spaces
        name = re.sub(r'[^a-z0-9]', '', name)
        return name
    
    def _generate_domain_candidates(self, company_name: str) -> List[str]:
        """Generate possible domain names for a company."""
        candidates = []
        normalized_name = self._normalize_company_name(company_name)
        
        # Generate domain patterns
        for pattern in self.domain_patterns:
            candidates.append(pattern.format(company=normalized_name))
        
        # Add variations with common words removed
        words = company_name.lower().split()
        if len(words) > 1:
            # Try first word only
            first_word = self._normalize_company_name(words[0])
            for pattern in self.domain_patterns:
                candidates.append(pattern.format(company=first_word))
            
            # Try first two words
            if len(words) >= 2:
                first_two = self._normalize_company_name(' '.join(words[:2]))
                for pattern in self.domain_patterns:
                    candidates.append(pattern.format(company=first_two))
        
        return list(set(candidates))
    
    async def _check_domain_exists(self, domain: str) -> bool:
        """Check if a domain exists."""
        try:
            # Remove protocol if present
            if domain.startswith(('http://', 'https://')):
                domain = domain.split('://', 1)[1]
            
            # Remove path if present
            domain = domain.split('/')[0]
            
            # Try DNS resolution
            dns.resolver.resolve(domain, 'A')
            return True
        except Exception:
            return False
    
    async def _validate_website(self, url: str) -> Tuple[bool, Optional[str]]:
        """Validate if a URL is a working website."""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            async with self.session.get(url, timeout=10, allow_redirects=True) as response:
                if response.status == 200:
                    # Get the final URL after redirects
                    final_url = str(response.url)
                    
                    # Check if it's a valid company website (not a parked domain)
                    content = await response.text()
                    if self._is_valid_company_website(content, url):
                        return True, final_url
                
                return False, None
                
        except Exception as e:
            logger.debug(f"Error validating {url}: {e}")
            return False, None
    
    def _is_valid_company_website(self, content: str, url: str) -> bool:
        """Check if content looks like a valid company website."""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check for common indicators of a real company website
        indicators = [
            'contact us',
            'about us',
            'our team',
            'careers',
            'blog',
            'news',
            'products',
            'services',
            'pricing',
            'login',
            'sign up'
        ]
        
        text_lower = soup.get_text().lower()
        indicator_count = sum(1 for indicator in indicators if indicator in text_lower)
        
        # Check for parked domain indicators
        parked_indicators = [
            'domain for sale',
            'buy this domain',
            'domain parking',
            'this domain may be for sale',
            'domain name sales',
            'domain broker'
        ]
        
        parked_count = sum(1 for indicator in parked_indicators if indicator in text_lower)
        
        # Valid if we have company indicators and no parked indicators
        return indicator_count > 2 and parked_count == 0
    
    async def _search_for_website(self, company_name: str) -> Optional[str]:
        """Search for company website using search engines."""
        search_queries = [
            f'"{company_name}" official website',
            f'"{company_name}" company website',
            f'"{company_name}" homepage',
            f'"{company_name}" site:com',
            f'"{company_name}" site:io'
        ]
        
        for query in search_queries:
            try:
                # Use a simple search approach (in real implementation, you'd use search APIs)
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                
                async with self.session.get(search_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Extract URLs from search results
                        urls = re.findall(r'https?://[^\s<>"]+', content)
                        
                        for url in urls:
                            # Filter for likely company websites
                            if self._looks_like_company_website(url, company_name):
                                is_valid, final_url = await self._validate_website(url)
                                if is_valid:
                                    return final_url
                                
            except Exception as e:
                logger.debug(f"Error searching for {company_name}: {e}")
                continue
        
        return None
    
    def _looks_like_company_website(self, url: str, company_name: str) -> bool:
        """Check if URL looks like it could be the company's website."""
        # Skip common non-company domains
        skip_domains = [
            'google.com', 'facebook.com', 'twitter.com', 'linkedin.com',
            'youtube.com', 'instagram.com', 'wikipedia.org', 'crunchbase.com',
            'angel.co', 'pitchbook.com', 'techcrunch.com', 'venturebeat.com'
        ]
        
        domain = urlparse(url).netloc.lower()
        for skip_domain in skip_domains:
            if skip_domain in domain:
                return False
        
        # Check if company name appears in domain
        company_words = company_name.lower().split()
        for word in company_words:
            if len(word) > 2 and word in domain:
                return True
        
        return False
    
    async def find_company_website(self, company_name: str) -> Optional[str]:
        """Find the official website for a company."""
        logger.info(f"Finding website for: {company_name}")
        
        # Step 1: Generate domain candidates and check them
        domain_candidates = self._generate_domain_candidates(company_name)
        
        for domain in domain_candidates:
            if await self._check_domain_exists(domain):
                is_valid, final_url = await self._validate_website(domain)
                if is_valid:
                    logger.info(f"Found valid website for {company_name}: {final_url}")
                    return final_url
        
        # Step 2: Search for website if domain candidates don't work
        logger.info(f"Domain candidates failed for {company_name}, searching...")
        found_url = await self._search_for_website(company_name)
        
        if found_url:
            logger.info(f"Found website via search for {company_name}: {found_url}")
            return found_url
        
        logger.warning(f"No website found for {company_name}")
        return None
    
    async def find_websites_batch(self, company_names: List[str]) -> Dict[str, Optional[str]]:
        """Find websites for multiple companies in batch."""
        results = {}
        
        # Process in batches to avoid overwhelming servers
        batch_size = 5
        for i in range(0, len(company_names), batch_size):
            batch = company_names[i:i + batch_size]
            
            tasks = [self.find_company_website(name) for name in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error finding website for {name}: {result}")
                    results[name] = None
                else:
                    results[name] = result
            
            # Add delay between batches
            if i + batch_size < len(company_names):
                await asyncio.sleep(2)
        
        return results

# Enhanced portfolio scraper with website finding
class EnhancedPortfolioScraper:
    """Enhanced portfolio scraper with website discovery."""
    
    def __init__(self):
        self.website_finder = None
    
    async def enhance_portfolio_with_websites(self, companies: List) -> List:
        """Enhance portfolio companies with website information."""
        if not self.website_finder:
            self.website_finder = WebsiteFinder()
        
        async with self.website_finder:
            company_names = [comp.name for comp in companies]
            websites = await self.website_finder.find_websites_batch(company_names)
            
            # Update companies with website information
            for company in companies:
                if company.name in websites and websites[company.name]:
                    company.website = websites[company.name]
                    logger.info(f"Enhanced {company.name} with website: {company.website}")
            
            return companies

async def main():
    """Test the website finder."""
    async with WebsiteFinder() as finder:
        test_companies = [
            "Snapdeal",
            "Delhivery", 
            "PubMatic",
            "Razorpay",
            "Unacademy"
        ]
        
        print("🔍 Testing Website Finder")
        print("=" * 40)
        
        for company in test_companies:
            website = await finder.find_company_website(company)
            if website:
                print(f"✅ {company}: {website}")
            else:
                print(f"❌ {company}: No website found")

if __name__ == "__main__":
    asyncio.run(main()) 