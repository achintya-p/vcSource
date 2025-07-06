"""
LinkedIn scraper for finding early-stage startup founders and companies.
"""
import time
import random
import hashlib
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import asyncio

from utils.config import get_settings
from utils.logger import get_logger
from data.schemas import CompanyProfile, FounderProfile, StartupProfile, SearchCriteria

logger = get_logger(__name__)
settings = get_settings()

class LinkedInScraper:
    """LinkedIn scraper for sourcing early-stage startups."""
    
    def __init__(self, use_mock_data: bool = True):
        self.session = requests.Session()
        self.driver = None
        self.base_url = "https://www.linkedin.com"
        self.use_mock_data = use_mock_data
        self.setup_session()
        
        # Mock data for testing
        self.mock_startups = self._create_mock_startups()
    
    def _create_mock_startups(self) -> Dict[str, List[StartupProfile]]:
        """Create mock startup data for testing."""
        mock_data = {}
        
        # AI/ML startups
        ai_startups = []
        for i in range(15):
            company = CompanyProfile(
                name=f"AI Solutions {i+1}",
                description=f"AI-powered platform for enterprise automation and decision making. Using machine learning to optimize business processes and drive innovation.",
                industry="AI/ML",
                location="San Francisco, CA" if i < 8 else "New York, NY",
                funding_stage="Seed" if i < 8 else "Series A",
                website=f"https://aisolutions{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/aisolutions{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Dr. Sarah Chen {i+1}",
                title="CEO & Co-Founder",
                company=f"AI Solutions {i+1}",
                experience=f"Former ML Engineer at Google, PhD in Computer Science from Stanford. Previously founded TechCorp {i+1} and led AI initiatives at Fortune 500 companies.",
                education="PhD Computer Science, Stanford University",
                linkedin_connections=800 + i*50,
                endorsements=45 + i*3,
                linkedin_url=f"https://linkedin.com/in/sarahchen{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            ai_startups.append(startup)
        
        # AI/ML keywords
        mock_data["AI"] = ai_startups
        mock_data["ai"] = ai_startups
        mock_data["machine learning"] = ai_startups
        mock_data["ML"] = ai_startups
        mock_data["artificial intelligence"] = ai_startups
        mock_data["AI startup"] = ai_startups
        mock_data["ML platform"] = ai_startups
        mock_data["AI SaaS"] = ai_startups
        mock_data["AI enterprise"] = ai_startups
        mock_data["AI fintech"] = ai_startups
        
        # Fintech startups
        fintech_startups = []
        for i in range(15):
            company = CompanyProfile(
                name=f"FinTech Pro {i+1}",
                description=f"Revolutionary fintech platform for digital payments and financial services. Democratizing access to financial tools and enabling financial inclusion.",
                industry="Fintech",
                location="New York, NY" if i < 8 else "London, UK",
                funding_stage="Seed" if i < 8 else "Series A",
                website=f"https://fintechpro{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/fintechpro{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Michael Rodriguez {i+1}",
                title="Founder & CEO",
                company=f"FinTech Pro {i+1}",
                experience=f"Former VP at Goldman Sachs, MBA from Harvard. Led digital transformation at BankCorp {i+1} and has 15+ years in financial services.",
                education="MBA, Harvard Business School",
                linkedin_connections=1200 + i*100,
                endorsements=60 + i*5,
                linkedin_url=f"https://linkedin.com/in/michaelrodriguez{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            fintech_startups.append(startup)
        
        # Fintech keywords
        mock_data["fintech"] = fintech_startups
        mock_data["Fintech"] = fintech_startups
        mock_data["financial technology"] = fintech_startups
        mock_data["payments"] = fintech_startups
        mock_data["banking"] = fintech_startups
        mock_data["insurtech"] = fintech_startups
        mock_data["wealthtech"] = fintech_startups
        mock_data["regtech"] = fintech_startups
        mock_data["cryptocurrency"] = fintech_startups
        
        # SaaS startups
        saas_startups = []
        for i in range(15):
            company = CompanyProfile(
                name=f"CloudWorks {i+1}",
                description=f"Enterprise SaaS platform for team collaboration and project management. Built for modern remote teams with advanced analytics and automation.",
                industry="SaaS",
                location="Austin, TX" if i < 8 else "Seattle, WA",
                funding_stage="Seed" if i < 8 else "Series A",
                website=f"https://cloudworks{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/cloudworks{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Alex Johnson {i+1}",
                title="CTO & Co-Founder",
                company=f"CloudWorks {i+1}",
                experience=f"Former Senior Engineer at Microsoft, built scalable systems at TechStartup {i+1}. Expert in cloud architecture and distributed systems.",
                education="BS Computer Science, MIT",
                linkedin_connections=600 + i*75,
                endorsements=35 + i*4,
                linkedin_url=f"https://linkedin.com/in/alexjohnson{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            saas_startups.append(startup)
        
        # SaaS keywords
        mock_data["SaaS"] = saas_startups
        mock_data["saas"] = saas_startups
        mock_data["software as a service"] = saas_startups
        mock_data["enterprise"] = saas_startups
        mock_data["b2b"] = saas_startups
        mock_data["enterprise software"] = saas_startups
        mock_data["B2B SaaS"] = saas_startups
        mock_data["cloud software"] = saas_startups
        mock_data["subscription software"] = saas_startups
        mock_data["business software"] = saas_startups
        mock_data["enterprise SaaS"] = saas_startups
        mock_data["workflow automation"] = saas_startups
        mock_data["software"] = saas_startups
        mock_data["platform"] = saas_startups[:5] + ai_startups[:5] + fintech_startups[:5]
        
        # Healthcare startups
        healthcare_startups = []
        for i in range(12):
            company = CompanyProfile(
                name=f"HealthTech {i+1}",
                description=f"Digital health platform for patient monitoring and telemedicine. Improving healthcare access and outcomes through innovative technology solutions.",
                industry="Healthcare",
                location="Boston, MA" if i < 6 else "San Diego, CA",
                funding_stage="Seed" if i < 7 else "Series A",
                website=f"https://healthtech{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/healthtech{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Dr. Emily Watson {i+1}",
                title="CEO & Founder",
                company=f"HealthTech {i+1}",
                experience=f"Former physician at Mayo Clinic, MD from Johns Hopkins. Passionate about healthcare innovation and improving patient outcomes.",
                education="MD, Johns Hopkins University",
                linkedin_connections=400 + i*60,
                endorsements=25 + i*3,
                linkedin_url=f"https://linkedin.com/in/emilywatson{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            healthcare_startups.append(startup)
        
        # Healthcare keywords
        mock_data["healthcare"] = healthcare_startups
        mock_data["HealthTech"] = healthcare_startups
        mock_data["digital health"] = healthcare_startups
        mock_data["telemedicine"] = healthcare_startups
        mock_data["medtech"] = healthcare_startups
        mock_data["healthtech"] = healthcare_startups
        mock_data["biotech"] = healthcare_startups
        mock_data["pharmaceuticals"] = healthcare_startups
        mock_data["medical devices"] = healthcare_startups
        
        # E-commerce startups
        ecommerce_startups = []
        for i in range(10):
            company = CompanyProfile(
                name=f"ShopSmart {i+1}",
                description=f"Next-generation e-commerce platform with AI-powered recommendations and seamless checkout experience. Revolutionizing online shopping.",
                industry="E-commerce",
                location="Los Angeles, CA" if i < 5 else "Miami, FL",
                funding_stage="Seed" if i < 6 else "Series A",
                website=f"https://shopsmart{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/shopsmart{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Jessica Kim {i+1}",
                title="Founder & CEO",
                company=f"ShopSmart {i+1}",
                experience=f"Former Product Manager at Amazon, MBA from Wharton. Built successful e-commerce businesses and has deep expertise in consumer behavior.",
                education="MBA, Wharton School",
                linkedin_connections=900 + i*80,
                endorsements=50 + i*4,
                linkedin_url=f"https://linkedin.com/in/jessicakim{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            ecommerce_startups.append(startup)
        
        # Consumer/E-commerce keywords
        mock_data["ecommerce"] = ecommerce_startups
        mock_data["E-commerce"] = ecommerce_startups
        mock_data["retail"] = ecommerce_startups
        mock_data["marketplace"] = ecommerce_startups
        mock_data["B2C"] = ecommerce_startups
        mock_data["consumer tech"] = ecommerce_startups
        mock_data["mobile app"] = ecommerce_startups
        mock_data["social media"] = ecommerce_startups
        mock_data["gaming"] = ecommerce_startups
        mock_data["entertainment"] = ecommerce_startups
        
        # Cybersecurity startups
        cybersecurity_startups = []
        for i in range(8):
            company = CompanyProfile(
                name=f"SecureNet {i+1}",
                description=f"Advanced cybersecurity platform protecting enterprises from evolving threats. Using AI and machine learning for threat detection and prevention.",
                industry="Cybersecurity",
                location="Washington, DC" if i < 4 else "San Francisco, CA",
                funding_stage="Seed" if i < 5 else "Series A",
                website=f"https://securenet{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/securenet{i+1}"
            )
            
            founder = FounderProfile(
                name=f"David Park {i+1}",
                title="CTO & Co-Founder",
                company=f"SecureNet {i+1}",
                experience=f"Former Security Engineer at NSA, PhD in Computer Security from Carnegie Mellon. Expert in cryptography and threat intelligence.",
                education="PhD Computer Security, Carnegie Mellon University",
                linkedin_connections=500 + i*70,
                endorsements=30 + i*3,
                linkedin_url=f"https://linkedin.com/in/davidpark{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            cybersecurity_startups.append(startup)
        
        mock_data["cybersecurity"] = cybersecurity_startups
        mock_data["security"] = cybersecurity_startups
        mock_data["cyber"] = cybersecurity_startups
        
        # Add additional keywords that might be searched (case-sensitive)
        mock_data["silicon valley"] = ai_startups + saas_startups
        mock_data["san francisco"] = ai_startups + saas_startups
        mock_data["bay area"] = ai_startups + saas_startups
        mock_data["enterprise"] = saas_startups + cybersecurity_startups
        mock_data["Enterprise"] = saas_startups + cybersecurity_startups
        mock_data["Consumer"] = ecommerce_startups
        mock_data["consumer"] = ecommerce_startups
        mock_data["financial technology"] = fintech_startups
        mock_data["telemedicine"] = healthcare_startups
        mock_data["mumbai"] = fintech_startups + ecommerce_startups
        mock_data["india"] = fintech_startups + ecommerce_startups
        mock_data["indian"] = fintech_startups + ecommerce_startups
        mock_data["Healthcare"] = healthcare_startups
        mock_data["Fintech"] = fintech_startups
        mock_data["AI/ML"] = ai_startups
        mock_data["artificial intelligence"] = ai_startups
        mock_data["software"] = saas_startups
        mock_data["payments"] = fintech_startups
        mock_data["banking"] = fintech_startups
        mock_data["medtech"] = healthcare_startups
        mock_data["B2B"] = saas_startups
        mock_data["software as a service"] = saas_startups
        mock_data["digital health"] = healthcare_startups
        
        # Stage-specific keywords
        mock_data["early stage"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        mock_data["startup"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        mock_data["emerging company"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        mock_data["growth stage"] = ai_startups[5:10] + fintech_startups[5:10] + saas_startups[5:10]
        mock_data["scaling"] = ai_startups[5:10] + fintech_startups[5:10] + saas_startups[5:10]
        mock_data["product market fit"] = ai_startups[5:10] + fintech_startups[5:10] + saas_startups[5:10]
        
        # Thesis-based keywords
        mock_data["category-defining"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["breakthrough"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["innovative"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["disruptive"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["digital"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["automation"] = ai_startups[:3] + saas_startups[:3]
        mock_data["analytics"] = ai_startups[:3] + saas_startups[:3]
        mock_data["data"] = ai_startups[:3] + saas_startups[:3]
        mock_data["cloud"] = saas_startups[:3]
        mock_data["mobile"] = ecommerce_startups[:3]
        mock_data["web"] = saas_startups[:3]
        
        # EdTech startups
        edtech_startups = []
        for i in range(8):
            company = CompanyProfile(
                name=f"LearnTech {i+1}",
                description=f"Innovative educational technology platform making learning accessible and engaging. Personalized learning experiences powered by AI.",
                industry="EdTech",
                location="Boston, MA" if i < 4 else "Austin, TX",
                funding_stage="Seed" if i < 5 else "Series A",
                website=f"https://learntech{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/learntech{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Dr. Maria Garcia {i+1}",
                title="CEO & Founder",
                company=f"LearnTech {i+1}",
                experience=f"Former Professor at MIT, PhD in Education Technology. Passionate about democratizing education and improving learning outcomes.",
                education="PhD Education Technology, MIT",
                linkedin_connections=600 + i*60,
                endorsements=40 + i*4,
                linkedin_url=f"https://linkedin.com/in/mariagarcia{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            edtech_startups.append(startup)
        
        mock_data["edtech"] = edtech_startups
        mock_data["education"] = edtech_startups
        mock_data["learning"] = edtech_startups
        
        # CleanTech startups
        cleantech_startups = []
        for i in range(6):
            company = CompanyProfile(
                name=f"GreenTech {i+1}",
                description=f"Sustainable technology solutions for renewable energy and environmental conservation. Building a cleaner, greener future.",
                industry="CleanTech",
                location="San Francisco, CA" if i < 3 else "Denver, CO",
                funding_stage="Seed" if i < 4 else "Series A",
                website=f"https://greentech{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/greentech{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Dr. Robert Chen {i+1}",
                title="Founder & CEO",
                company=f"GreenTech {i+1}",
                experience=f"Former Research Scientist at Tesla, PhD in Environmental Engineering from UC Berkeley. Expert in renewable energy systems.",
                education="PhD Environmental Engineering, UC Berkeley",
                linkedin_connections=700 + i*80,
                endorsements=45 + i*5,
                linkedin_url=f"https://linkedin.com/in/robertchen{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            cleantech_startups.append(startup)
        
        mock_data["cleantech"] = cleantech_startups
        mock_data["green tech"] = cleantech_startups
        mock_data["renewable energy"] = cleantech_startups
        mock_data["sustainability"] = cleantech_startups
        
        # Biotech startups
        biotech_startups = []
        for i in range(6):
            company = CompanyProfile(
                name=f"BioTech {i+1}",
                description=f"Cutting-edge biotechnology company developing breakthrough therapies and diagnostic tools. Advancing the future of medicine.",
                industry="Biotech",
                location="San Diego, CA" if i < 3 else "Cambridge, MA",
                funding_stage="Seed" if i < 4 else "Series A",
                website=f"https://biotech{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/biotech{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Dr. Lisa Thompson {i+1}",
                title="CSO & Co-Founder",
                company=f"BioTech {i+1}",
                experience=f"Former Research Director at Genentech, PhD in Molecular Biology from Harvard. Published 50+ papers in leading journals.",
                education="PhD Molecular Biology, Harvard University",
                linkedin_connections=500 + i*70,
                endorsements=35 + i*4,
                linkedin_url=f"https://linkedin.com/in/lisathompson{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            biotech_startups.append(startup)
        
        mock_data["biotech"] = biotech_startups
        mock_data["biotechnology"] = biotech_startups
        mock_data["life sciences"] = biotech_startups
        
        # Indian startups (for Nexus Venture Partners)
        indian_startups = []
        for i in range(12):
            company = CompanyProfile(
                name=f"TechCorp India {i+1}",
                description=f"Innovative technology company building solutions for the Indian market. Focused on digital transformation and local market needs.",
                industry="SaaS" if i < 4 else "Fintech" if i < 8 else "AI/ML",
                location="Bangalore, India" if i < 6 else "Mumbai, India",
                funding_stage="Seed" if i < 8 else "Series A",
                website=f"https://techcorpindia{i+1}.com",
                linkedin_url=f"https://linkedin.com/company/techcorpindia{i+1}"
            )
            
            founder = FounderProfile(
                name=f"Rajesh Kumar {i+1}",
                title="CEO & Co-Founder",
                company=f"TechCorp India {i+1}",
                experience=f"Former Senior Engineer at {['Google', 'Microsoft', 'Amazon', 'Flipkart'][i % 4]}, IIT graduate with 8+ years in technology. Previously founded successful startups in India.",
                education="BTech Computer Science, IIT {0}".format(['Delhi', 'Bombay', 'Madras', 'Kanpur'][i % 4]),
                linkedin_connections=600 + i*80,
                endorsements=40 + i*5,
                linkedin_url=f"https://linkedin.com/in/rajeshkumar{i+1}"
            )
            
            startup = StartupProfile(company=company, founders=[founder])
            indian_startups.append(startup)
        
        mock_data["india"] = indian_startups
        mock_data["indian"] = indian_startups
        mock_data["bangalore"] = indian_startups
        mock_data["mumbai"] = indian_startups
        
        # Add more Indian/Asia/other geographies
        india_startups = []
        for i in range(10):
            company = CompanyProfile(
                name=f"BharatTech {i+1}",
                description=f"Indian tech startup focused on digital transformation and financial inclusion.",
                industry="Fintech",
                location="Bangalore, India",
                funding_stage="Seed" if i < 5 else "Series A",
                website=f"https://bharattech{i+1}.in",
                linkedin_url=f"https://linkedin.com/company/bharattech{i+1}"
            )
            founder = FounderProfile(
                name=f"Ankit Sharma {i+1}",
                title="Founder & CEO",
                company=f"BharatTech {i+1}",
                experience=f"Built BharatTech {i+1} from the ground up, ex-Flipkart, IIT Bombay.",
                education="BTech, IIT Bombay",
                linkedin_connections=700 + i*30,
                endorsements=20 + i*2,
                linkedin_url=f"https://linkedin.com/in/ankitsharma{i+1}"
            )
            startup = StartupProfile(company=company, founders=[founder])
            india_startups.append(startup)
        mock_data["india"] = india_startups
        mock_data["indian"] = india_startups
        mock_data["bangalore"] = india_startups
        mock_data["mumbai"] = india_startups
        mock_data["fintech india"] = india_startups
        
        # Add cross-category keywords (after all startup lists are created)
        mock_data["startup"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        mock_data["tech startup"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        mock_data["technology"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        mock_data["innovation"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        
        # Stage-specific keywords
        mock_data["early stage"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        mock_data["emerging company"] = ai_startups[:5] + fintech_startups[:5] + saas_startups[:5]
        mock_data["growth stage"] = ai_startups[5:10] + fintech_startups[5:10] + saas_startups[5:10]
        mock_data["scaling"] = ai_startups[5:10] + fintech_startups[5:10] + saas_startups[5:10]
        mock_data["product market fit"] = ai_startups[5:10] + fintech_startups[5:10] + saas_startups[5:10]
        
        # Thesis-based keywords
        mock_data["category-defining"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["breakthrough"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["innovative"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["disruptive"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["digital"] = ai_startups[:3] + fintech_startups[:3] + saas_startups[:3]
        mock_data["automation"] = ai_startups[:3] + saas_startups[:3]
        mock_data["analytics"] = ai_startups[:3] + saas_startups[:3]
        mock_data["data"] = ai_startups[:3] + saas_startups[:3]
        mock_data["cloud"] = saas_startups[:3]
        mock_data["mobile"] = ecommerce_startups[:3]
        mock_data["web"] = saas_startups[:3]
        
        return mock_data
    
    def setup_session(self):
        """Setup session with headers and cookies."""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def setup_driver(self):
        """Setup Selenium WebDriver for dynamic content."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={self.session.headers['User-Agent']}")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
    
    async def search_startups(self, keyword: str, max_count: int = 50) -> List[StartupProfile]:
        """Search for startups based on keyword."""
        logger.info(f"Searching for startups with keyword: {keyword}")
        
        if self.use_mock_data:
            return await self._search_startups_mock(keyword, max_count)
        
        try:
            # First, search for companies
            companies = await self._search_companies(keyword, max_count)
            
            # Then get detailed profiles for each company
            startups = []
            for company in companies[:max_count]:
                try:
                    startup_profile = await self._get_startup_profile(company)
                    if startup_profile:
                        startups.append(startup_profile)
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.warning(f"Error getting profile for {company.get('name', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(startups)} startup profiles")
            return startups
            
        except Exception as e:
            logger.error(f"Error searching startups for '{keyword}': {e}")
            return []
    
    async def _search_startups_mock(self, keyword: str, max_count: int) -> List[StartupProfile]:
        """Search for startups using mock data (case-insensitive, robust fallback)."""
        logger.info(f"Using mock data for keyword: {keyword}")
        
        # Lowercase the keyword for matching
        keyword_lc = keyword.lower()
        
        # Build a lowercase-keyed version of the mock data
        mock_data_lc = {k.lower(): v for k, v in self.mock_startups.items()}
        
        # Find matching startups
        matching_startups = []
        
        # First try exact match
        if keyword_lc in mock_data_lc:
            matching_startups = mock_data_lc[keyword_lc]
        else:
            # Check partial matches
            for mock_keyword, startups in mock_data_lc.items():
                if keyword_lc in mock_keyword or mock_keyword in keyword_lc:
                    matching_startups.extend(startups)
        
        # If still no matches, try broader matching
        if not matching_startups:
            # Map common keywords to categories
            keyword_mapping = {
                'indian': 'india',
                'fintech': 'fintech',
                'ai': 'ai',
                'machine learning': 'ai',
                'ml': 'ai',
                'artificial intelligence': 'ai',
                'saas': 'saas',
                'software': 'saas',
                'enterprise': 'saas',
                'b2b': 'saas',
                'consumer': 'ecommerce',
                'b2c': 'ecommerce',
                'ecommerce': 'ecommerce',
                'marketplace': 'ecommerce',
                'healthcare': 'healthcare',
                'healthtech': 'healthcare',
                'telemedicine': 'healthcare',
                'medtech': 'healthcare',
                'payments': 'fintech',
                'banking': 'fintech',
                'financial technology': 'fintech',
                'cybersecurity': 'cybersecurity',
                'security': 'cybersecurity',
                'silicon valley': 'ai',
                'san francisco': 'ai',
                'bay area': 'ai',
                'bangalore': 'india',
                'mumbai': 'india',
                'india': 'india',
                'digital health': 'healthcare',
                'healthcare': 'healthcare'
            }
            
            mapped_key = keyword_mapping.get(keyword_lc)
            if mapped_key and mapped_key in mock_data_lc:
                matching_startups = mock_data_lc[mapped_key]
                logger.info(f"Mapped '{keyword}' to '{mapped_key}' and found {len(matching_startups)} startups")
            else:
                logger.warning(f"No mapping found for keyword '{keyword}'")
        
        # If no matches found, return some random startups
        if not matching_startups:
            logger.info(f"No mock data found for '{keyword}', returning random startups")
            all_startups = []
            for startups in mock_data_lc.values():
                all_startups.extend(startups)
            
            if all_startups:
                matching_startups = random.sample(all_startups, min(max_count, len(all_startups)))
            else:
                # Create some basic startups if no mock data exists
                logger.warning("No mock startups available, creating basic ones")
                for i in range(max_count):
                    company = CompanyProfile(
                        name=f"Startup {i+1}",
                        description=f"Early-stage startup in {keyword} space",
                        industry="Technology",
                        location="Bangalore, India",
                        funding_stage="Seed",
                        website=f"https://startup{i+1}.com",
                        linkedin_url=f"https://linkedin.com/company/startup{i+1}"
                    )
                    founder = FounderProfile(
                        name=f"Founder {i+1}",
                        title="CEO & Founder",
                        company=f"Startup {i+1}",
                        experience=f"Experienced entrepreneur in {keyword}",
                        education="Bachelor's Degree",
                        linkedin_connections=500,
                        endorsements=25,
                        linkedin_url=f"https://linkedin.com/in/founder{i+1}"
                    )
                    startup = StartupProfile(company=company, founders=[founder])
                    matching_startups.append(startup)
        
        # Limit results
        result = matching_startups[:max_count]
        logger.info(f"Found {len(result)} mock startups for '{keyword}'")
        return result
    
    async def _search_companies(self, keyword: str, max_count: int) -> List[Dict]:
        """Search for companies on LinkedIn."""
        companies = []
        
        try:
            # Build search URL
            search_url = f"{self.base_url}/search/results/companies/"
            params = {
                'keywords': keyword,
                'origin': 'GLOBAL_SEARCH_HEADER'
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            companies = self._parse_company_results(soup, max_count)
            
        except Exception as e:
            logger.error(f"Error searching companies for '{keyword}': {e}")
        
        return companies
    
    def _parse_company_results(self, soup: BeautifulSoup, max_count: int) -> List[Dict]:
        """Parse company search results."""
        companies = []
        
        try:
            # Find company cards
            company_cards = soup.find_all('div', class_='entity-result__item')
            
            for card in company_cards[:max_count]:
                try:
                    company_data = self._extract_company_card_data(card)
                    if company_data:
                        companies.append(company_data)
                except Exception as e:
                    logger.warning(f"Error parsing company card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing company results: {e}")
        
        return companies
    
    def _extract_company_card_data(self, card) -> Optional[Dict]:
        """Extract company data from a search result card."""
        try:
            # Extract company name
            name_elem = card.find('span', class_='entity-result__title-text')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            # Extract industry
            industry_elem = card.find('p', class_='entity-result__primary-subtitle')
            industry = industry_elem.get_text(strip=True) if industry_elem else None
            
            # Extract location
            location_elem = card.find('p', class_='entity-result__secondary-subtitle')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Extract company URL
            link_elem = card.find('a', class_='app-aware-link')
            company_url = urljoin(self.base_url, link_elem['href']) if link_elem else None
            
            if name:
                return {
                    'name': name,
                    'industry': industry,
                    'location': location,
                    'url': company_url
                }
            
        except Exception as e:
            logger.warning(f"Error extracting company data: {e}")
        
        return None
    
    async def _get_startup_profile(self, company_data: Dict) -> Optional[StartupProfile]:
        """Get detailed startup profile including founders."""
        try:
            company_name = company_data['name']
            
            # Get company profile
            company_profile = await self._get_company_profile(company_name)
            if not company_profile:
                return None
            
            # Get founders
            founders = await self._get_company_founders(company_name)
            
            # Create startup profile
            startup_profile = StartupProfile(
                company=company_profile,
                founders=founders
            )
            
            return startup_profile
            
        except Exception as e:
            logger.warning(f"Error getting startup profile for {company_data.get('name', 'Unknown')}: {e}")
            return None
    
    async def _get_company_profile(self, company_name: str) -> Optional[CompanyProfile]:
        """Get company profile details."""
        try:
            # For now, create a basic company profile
            # In a real implementation, you'd scrape the company page
            company_profile = CompanyProfile(
                name=company_name,
                description=f"Early-stage startup in {company_name}",
                industry="Technology",  # Default
                location="San Francisco, CA",  # Default
                funding_stage="Seed",
                website=f"https://{company_name.lower().replace(' ', '')}.com",
                linkedin_url=f"https://linkedin.com/company/{company_name.lower().replace(' ', '')}"
            )
            
            return company_profile
            
        except Exception as e:
            logger.warning(f"Error getting company profile for {company_name}: {e}")
            return None
    
    async def _get_company_founders(self, company_name: str) -> List[FounderProfile]:
        """Get founders for a company."""
        founders = []
        
        try:
            # Search for founders of this company
            founder_keywords = [
                f"founder {company_name}",
                f"co-founder {company_name}",
                f"CEO {company_name}",
                f"CTO {company_name}"
            ]
            
            for keyword in founder_keywords:
                try:
                    # For now, create mock founder profiles
                    # In a real implementation, you'd search and scrape founder profiles
                    founder = FounderProfile(
                        name=f"Founder of {company_name}",
                        title="Founder & CEO",
                        company=company_name,
                        experience=f"Experienced entrepreneur and founder of {company_name}",
                        education="Bachelor's in Computer Science",
                        linkedin_connections=500,
                        endorsements=25,
                        linkedin_url=f"https://linkedin.com/in/founder-{company_name.lower().replace(' ', '')}"
                    )
                    founders.append(founder)
                    
                    # Only add one founder per company for now
                    break
                    
                except Exception as e:
                    logger.warning(f"Error getting founder for {keyword}: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"Error getting founders for {company_name}: {e}")
        
        return founders

    def login(self, email: str, password: str) -> bool:
        """Login to LinkedIn."""
        try:
            if not self.driver:
                self.setup_driver()
            
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for login form
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            
            # Enter credentials
            email_field.send_keys(email)
            password_field.send_keys(password)
            
            # Submit form
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            
            logger.info("Successfully logged into LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"Failed to login to LinkedIn: {e}")
            return False
    
    def search_founders(self, criteria: SearchCriteria) -> List[Dict]:
        """Search for founders based on criteria."""
        founders = []
        
        # Build search queries
        search_queries = self._build_search_queries(criteria)
        
        for query in search_queries:
            try:
                logger.info(f"Searching for: {query}")
                results = self._search_people(query)
                founders.extend(results)
                
                # Rate limiting
                time.sleep(random.uniform(settings.SCRAPING_DELAY, settings.SCRAPING_DELAY * 2))
                
            except Exception as e:
                logger.error(f"Error searching for {query}: {e}")
                continue
        
        return founders
    
    def _build_search_queries(self, criteria: SearchCriteria) -> List[str]:
        """Build search queries based on criteria."""
        queries = []
        
        # Base keywords for early-stage founders
        base_keywords = ["founder", "co-founder", "CEO", "CTO", "CPO", "startup"]
        
        # Add industry-specific keywords
        for industry in criteria.industries:
            for keyword in base_keywords:
                queries.append(f"{keyword} {industry}")
        
        # Add location-specific queries
        for location in criteria.locations:
            for keyword in base_keywords:
                queries.append(f"{keyword} {location}")
        
        # Add stage-specific queries
        for stage in criteria.stages:
            for keyword in base_keywords:
                queries.append(f"{keyword} {stage}")
        
        # Add custom keywords
        for keyword in criteria.keywords:
            queries.append(keyword)
        
        return list(set(queries))  # Remove duplicates
    
    def _search_people(self, query: str) -> List[Dict]:
        """Search for people on LinkedIn."""
        try:
            search_url = f"{self.base_url}/search/results/people/"
            params = {
                'keywords': query,
                'origin': 'GLOBAL_SEARCH_HEADER'
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_people_results(soup)
            
        except Exception as e:
            logger.error(f"Error searching people for {query}: {e}")
            return []
    
    async def search_people(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """Search for people on LinkedIn with mock data support."""
        if self.use_mock_data:
            return await self._search_people_mock(keyword, max_results)
        
        try:
            return self._search_people(keyword)[:max_results]
        except Exception as e:
            logger.error(f"Error in search_people: {e}")
            return []
    
    async def _search_people_mock(self, keyword: str, max_results: int) -> List[Dict]:
        """Mock people search results."""
        mock_people = []
        
        # Generate mock people based on keyword
        titles = ["CEO", "CTO", "Founder", "VP Engineering", "Head of Product", "Senior Engineer"]
        names = ["Alex Johnson", "Sarah Chen", "Michael Rodriguez", "Priya Patel", "David Kim", "Emily Watson"]
        locations = ["San Francisco, CA", "New York, NY", "London, UK", "Bangalore, India", "Austin, TX"]
        
        for i in range(min(max_results, 6)):
            person = {
                "name": names[i % len(names)],
                "title": titles[i % len(titles)],
                "profile_url": f"https://linkedin.com/in/person{i}",
                "experience": f"Previous experience in {keyword} space",
                "education": "Top university graduate",
                "location": locations[i % len(locations)],
                "endorsements": 50 + i * 10,
                "connections": 500 + i * 100
            }
            mock_people.append(person)
        
        return mock_people
    
    def _parse_people_results(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse people search results."""
        results = []
        
        # Find people cards
        people_cards = soup.find_all('div', class_='entity-result__item')
        
        for card in people_cards:
            try:
                person_data = self._extract_person_data(card)
                if person_data:
                    results.append(person_data)
            except Exception as e:
                logger.warning(f"Error parsing person card: {e}")
                continue
        
        return results
    
    def _extract_person_data(self, card) -> Optional[Dict]:
        """Extract person data from a search result card."""
        try:
            # Extract name
            name_elem = card.find('span', class_='entity-result__title-text')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            # Extract title
            title_elem = card.find('p', class_='entity-result__primary-subtitle')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract company
            company_elem = card.find('p', class_='entity-result__secondary-subtitle')
            company = company_elem.get_text(strip=True) if company_elem else None
            
            # Extract location
            location_elem = card.find('p', class_='entity-result__tertiary-subtitle')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Extract profile URL
            link_elem = card.find('a', class_='app-aware-link')
            profile_url = urljoin(self.base_url, link_elem['href']) if link_elem else None
            
            if name:
                return {
                    'name': name,
                    'title': title,
                    'company': company,
                    'location': location,
                    'profile_url': profile_url
                }
            
        except Exception as e:
            logger.warning(f"Error extracting person data: {e}")
        
        return None

    def get_founder_profile(self, profile_url: str) -> Optional[FounderProfile]:
        """Get detailed founder profile from LinkedIn."""
        try:
            if not self.driver:
                self.setup_driver()
            
            self.driver.get(profile_url)
            
            # Wait for profile to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card"))
            )
            
            profile_data = self._extract_profile_data()
            if profile_data:
                return FounderProfile(**profile_data)
            
        except Exception as e:
            logger.error(f"Error getting founder profile from {profile_url}: {e}")
        
        return None
    
    def _extract_profile_data(self) -> Optional[Dict]:
        """Extract profile data from LinkedIn page."""
        try:
            # Extract name
            name_elem = self.driver.find_element(By.CLASS_NAME, "text-heading-xlarge")
            name = name_elem.text.strip()
            
            # Extract title
            title_elem = self.driver.find_element(By.CLASS_NAME, "text-body-medium")
            title = title_elem.text.strip()
            
            # Extract company
            company_elem = self.driver.find_element(By.CLASS_NAME, "pv-text-details__right-panel")
            company = company_elem.text.strip()
            
            # Extract location
            location_elem = self.driver.find_element(By.CLASS_NAME, "text-body-small")
            location = location_elem.text.strip()
            
            # Extract connections
            connections_elem = self.driver.find_element(By.CLASS_NAME, "pv-top-card--list-bullet")
            connections_text = connections_elem.text.strip()
            connections = self._extract_connections_count(connections_text)
            
            # Extract experience
            experience = self._extract_experience()
            
            # Extract education
            education = self._extract_education()
            
            return {
                'name': name,
                'title': title,
                'company': company,
                'location': location,
                'linkedin_connections': connections,
                'experience': experience,
                'education': education,
                'linkedin_url': self.driver.current_url
            }
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            return None
    
    def _extract_connections_count(self, connections_text: str) -> Optional[int]:
        """Extract connections count from text."""
        try:
            import re
            match = re.search(r'(\d+)', connections_text)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.warning(f"Error extracting connections count: {e}")
        return None
    
    def _extract_experience(self) -> str:
        """Extract experience section."""
        try:
            experience_section = self.driver.find_element(By.ID, "experience")
            experience_items = experience_section.find_elements(By.CLASS_NAME, "pv-position-entity")
            
            experience_text = []
            for item in experience_items[:5]:  # Limit to 5 most recent
                try:
                    title = item.find_element(By.CLASS_NAME, "pv-entity__summary-info-v2").text.strip()
                    company = item.find_element(By.CLASS_NAME, "pv-entity__company-summary-info").text.strip()
                    experience_text.append(f"{title} at {company}")
                except:
                    continue
            
            return " | ".join(experience_text)
            
        except Exception as e:
            logger.warning(f"Error extracting experience: {e}")
            return ""
    
    def _extract_education(self) -> str:
        """Extract education section."""
        try:
            education_section = self.driver.find_element(By.ID, "education")
            education_items = education_section.find_elements(By.CLASS_NAME, "pv-education-entity")
            
            education_text = []
            for item in education_items[:3]:  # Limit to 3 most recent
                try:
                    school = item.find_element(By.CLASS_NAME, "pv-entity__school-name").text.strip()
                    degree = item.find_element(By.CLASS_NAME, "pv-entity__degree-name").text.strip()
                    education_text.append(f"{degree} from {school}")
                except:
                    continue
            
            return " | ".join(education_text)
            
        except Exception as e:
            logger.warning(f"Error extracting education: {e}")
            return ""
    
    def get_company_profile(self, company_name: str) -> Optional[CompanyProfile]:
        """Get company profile from LinkedIn."""
        try:
            # Search for company
            search_url = f"{self.base_url}/search/results/companies/"
            params = {'keywords': company_name}
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            company_data = self._extract_company_data(soup, company_name)
            
            if company_data:
                return CompanyProfile(**company_data)
            
        except Exception as e:
            logger.error(f"Error getting company profile for {company_name}: {e}")
        
        return None
    
    def _extract_company_data(self, soup: BeautifulSoup, company_name: str) -> Optional[Dict]:
        """Extract company data from search results."""
        try:
            # Find company in search results
            company_cards = soup.find_all('div', class_='entity-result__item')
            
            for card in company_cards:
                company_data = self._extract_company_card_data(card)
                if company_data and company_name.lower() in company_data['name'].lower():
                    return company_data
            
        except Exception as e:
            logger.error(f"Error extracting company data: {e}")
        
        return None
    
    def close(self):
        """Close the scraper and cleanup resources."""
        if self.driver:
            self.driver.quit()
        if self.session:
            self.session.close() 