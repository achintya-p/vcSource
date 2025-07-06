#!/usr/bin/env python3
"""
Unified VC Sourcing Agent
Combines portfolio scraping, startup sourcing, and talent sourcing in one system
"""
import asyncio
import time
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from portfolio_rag_scraper import PortfolioRAGScraper, FallbackPortfolioScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.vc_profile_scraper import VCProfileScraper
from models.optimized_fit_metric import OptimizedFitMetricCalculator
from metrics.quality_scorer import QualityScorer
from data.schemas import CompanyProfile, FounderProfile, StartupProfile, VCProfile, FitMetrics
from utils.logger import logger

@dataclass
class SourcingResult:
    """Unified result for VC sourcing."""
    vc_firm: str
    analysis_type: str  # "startup_sourcing" or "talent_sourcing"
    portfolio_companies: List[str]
    results: List[Dict]
    processing_time: float
    timestamp: datetime

class UnifiedVCSourcingAgent:
    """
    Unified VC Sourcing Agent
    
    This agent can:
    1. Scrape VC portfolio companies using RAG
    2. Find startups that match VC investment criteria
    3. Find talent for portfolio companies
    """
    
    def __init__(self, use_mock_data: bool = True):
        self.use_mock_data = use_mock_data
        
        # Core components
        self.linkedin_scraper = LinkedInScraper(use_mock_data=use_mock_data)
        self.vc_scraper = VCProfileScraper()
        self.fit_calculator = OptimizedFitMetricCalculator()
        self.quality_scorer = QualityScorer()
        
        # Portfolio and conflict detection
        self.portfolio_cache = {}
        
        logger.info("Unified VC Sourcing Agent initialized")
    
    async def source_startups_for_vc(
        self, 
        vc_firm: str, 
        max_startups: int = 50,
        show_all: bool = True,
        find_websites: bool = True
    ) -> SourcingResult:
        """
        Find startups that match a VC firm's investment criteria.
        
        This is the main startup sourcing functionality.
        """
        start_time = time.time()
        logger.info(f"Sourcing startups for {vc_firm}")
        
        try:
            # Step 1: Get VC profile
            vc_profile = await self.vc_scraper.scrape_vc_profile(vc_firm)
            if not vc_profile:
                raise ValueError(f"Could not find VC profile for {vc_firm}")
            
            # Step 2: Get portfolio summary for context
            portfolio_summary = await self._get_portfolio_summary(vc_firm)
            
            # Step 3: Generate search keywords
            search_keywords = self._generate_search_keywords(vc_profile)
            
            # Step 4: Search for startups
            all_startups = []
            
            # Check if we should use real data or mock data
            use_mock_data = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'
            
            if use_mock_data:
                # Use existing LinkedIn scraper with mock data
                startups_per_keyword = max(1, max_startups // len(search_keywords))
                for keyword in search_keywords:
                    startups = await self.linkedin_scraper.search_startups(
                        keyword, startups_per_keyword
                    )
                    all_startups.extend(startups)
            else:
                # Use real data scraper
                from real_data_scraper import RealDataScraper
                async with RealDataScraper() as real_scraper:
                    for keyword in search_keywords:
                        startups = await real_scraper.search_startups_multi_source(
                            keyword, max_startups // len(search_keywords)
                        )
                        all_startups.extend(startups)
            
            # Remove duplicates
            unique_startups = self._remove_duplicates(all_startups)
            logger.info(f"Found {len(unique_startups)} unique startups")
            
            # Step 5: Calculate fit metrics
            fit_metrics = self.fit_calculator.calculate_fit_metrics_batch(
                unique_startups, vc_profile
            )
            
            # Step 6: Calculate quality scores
            for startup in unique_startups:
                startup.quality_score = self.quality_scorer.calculate_quality_score(startup)
            
            # Step 7: Detect portfolio conflicts and calculate portfolio fit
            for startup in unique_startups:
                startup.portfolio_conflicts = await self._detect_portfolio_conflicts(startup, vc_firm)
                startup.portfolio_fit = await self._calculate_portfolio_fit(startup, vc_firm)
            
            # Step 8: Find websites for matched startups if requested
            if find_websites:
                unique_startups = await self._enhance_startups_with_websites(unique_startups)
            
            # Step 9: Create detailed analysis
            detailed_results = self._create_startup_analysis(
                fit_metrics, unique_startups, vc_profile
            )
            
            processing_time = time.time() - start_time
            
            return SourcingResult(
                vc_firm=vc_firm,
                analysis_type="startup_sourcing",
                portfolio_companies=portfolio_summary.get("companies", []),
                results=detailed_results,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error sourcing startups for {vc_firm}: {e}")
            raise
    
    async def source_talent_for_portfolio(
        self, 
        vc_firm: str, 
        max_talent_per_company: int = 10,
        platforms: List[str] = None
    ) -> SourcingResult:
        """
        Find talent for companies in a VC firm's portfolio.
        
        This is the talent sourcing functionality.
        """
        if platforms is None:
            platforms = ["linkedin", "crunchbase", "twitter"]
        
        start_time = time.time()
        logger.info(f"Sourcing talent for {vc_firm} portfolio")
        
        try:
            # Step 1: Get portfolio companies
            portfolio_companies = await self._get_portfolio_companies(vc_firm)
            
            if not portfolio_companies:
                raise ValueError(f"No portfolio companies found for {vc_firm}")
            
            logger.info(f"Found {len(portfolio_companies)} portfolio companies")
            
            # Step 2: Find talent for each portfolio company
            all_talent_results = []
            
            for company in portfolio_companies:
                logger.info(f"Finding talent for {company.name}")
                
                company_talent = await self._find_talent_for_company(
                    company, max_talent_per_company, platforms
                )
                
                all_talent_results.extend(company_talent)
            
            # Step 3: Sort by relevance score
            all_talent_results.sort(key=lambda x: x["match_score"], reverse=True)
            
            processing_time = time.time() - start_time
            
            return SourcingResult(
                vc_firm=vc_firm,
                analysis_type="talent_sourcing",
                portfolio_companies=[comp.name for comp in portfolio_companies],
                results=all_talent_results,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error sourcing talent for {vc_firm}: {e}")
            raise
    
    async def comprehensive_vc_analysis(
        self, 
        vc_firm: str, 
        max_startups: int = 50,
        max_talent: int = 10,
        platforms: List[str] = None
    ) -> Dict:
        """
        Run comprehensive analysis: both startup sourcing and talent sourcing.
        """
        logger.info(f"Running comprehensive analysis for {vc_firm}")
        
        # Run both analyses
        startup_results = await self.source_startups_for_vc(
            vc_firm, max_startups, show_all=True, find_websites=True
        )
        
        talent_results = await self.source_talent_for_portfolio(
            vc_firm, max_talent, platforms
        )
        
        return {
            "vc_firm": vc_firm,
            "analysis_timestamp": datetime.now().isoformat(),
            "startup_sourcing": {
                "portfolio_companies": startup_results.portfolio_companies,
                "total_startups_found": len(startup_results.results),
                "processing_time": startup_results.processing_time,
                "results": startup_results.results[:10]  # Top 10
            },
            "talent_sourcing": {
                "portfolio_companies": talent_results.portfolio_companies,
                "total_talent_found": len(talent_results.results),
                "processing_time": talent_results.processing_time,
                "results": talent_results.results[:10]  # Top 10
            }
        }
    
    # Helper methods
    async def _get_portfolio_companies(self, vc_firm: str, find_websites: bool = True) -> List:
        """Get portfolio companies using RAG with fallback and website enhancement."""
        if vc_firm in self.portfolio_cache:
            return self.portfolio_cache[vc_firm]
        
        # Try RAG scraper first with website enhancement
        if not self.use_mock_data:
            try:
                async with PortfolioRAGScraper() as rag_scraper:
                    if find_websites:
                        companies = await rag_scraper.scrape_portfolio_with_websites(vc_firm, max_companies=50)
                    else:
                        companies = await rag_scraper.scrape_portfolio(vc_firm, max_companies=50)
                    if companies:
                        self.portfolio_cache[vc_firm] = companies
                        return companies
            except Exception as e:
                logger.error(f"RAG scraper failed: {e}")
        
        # Fallback to fallback scraper
        fallback_scraper = FallbackPortfolioScraper()
        companies = await fallback_scraper.scrape_portfolio(vc_firm, max_companies=50)
        self.portfolio_cache[vc_firm] = companies
        return companies
    
    async def _get_portfolio_summary(self, vc_firm: str) -> Dict:
        """Get portfolio summary."""
        if not self.use_mock_data:
            try:
                async with PortfolioRAGScraper() as rag_scraper:
                    summary = await rag_scraper.get_portfolio_summary(vc_firm)
                    if summary and summary["total_companies"] > 0:
                        return summary
            except Exception as e:
                logger.error(f"RAG scraper failed: {e}")
        
        # Fallback
        fallback_scraper = FallbackPortfolioScraper()
        return await fallback_scraper.get_portfolio_summary(vc_firm)
    
    def _generate_search_keywords(self, vc_profile: VCProfile) -> List[str]:
        """Generate search keywords based on VC focus areas."""
        keywords = []
        
        # Add focus areas as keywords
        for focus_area in vc_profile.focus_areas:
            keywords.append(focus_area)
            
            # Add variations
            if focus_area.lower() == "ai/ml":
                keywords.extend(["AI", "machine learning", "artificial intelligence"])
            elif focus_area.lower() == "fintech":
                keywords.extend(["fintech", "financial technology", "payments", "banking"])
            elif focus_area.lower() == "saas":
                keywords.extend(["SaaS", "software as a service", "enterprise", "B2B"])
            elif focus_area.lower() == "healthcare":
                keywords.extend(["healthcare", "digital health", "telemedicine", "medtech"])
            elif focus_area.lower() == "consumer":
                keywords.extend(["consumer", "B2C", "marketplace", "ecommerce"])
            elif focus_area.lower() == "enterprise":
                keywords.extend(["enterprise", "B2B", "SaaS", "software"])
            elif focus_area.lower() == "technology":
                keywords.extend(["software", "AI", "machine learning", "platform", "tech"])
        
        # Remove duplicates and limit
        unique_keywords = list(set(keywords))[:12]
        
        logger.info(f"Generated keywords: {unique_keywords}")
        return unique_keywords
    
    def _remove_duplicates(self, startups: List[StartupProfile]) -> List[StartupProfile]:
        """Remove duplicate startups."""
        seen = set()
        unique_startups = []
        
        for startup in startups:
            company_name = startup.company.name.lower().strip()
            if company_name not in seen:
                seen.add(company_name)
                unique_startups.append(startup)
        
        return unique_startups
    
    async def _detect_portfolio_conflicts(self, startup: StartupProfile, vc_firm: str) -> Dict:
        """Detect conflicts with existing portfolio companies."""
        portfolio_companies = await self._get_portfolio_companies(vc_firm)
        
        conflicts = {
            "has_conflicts": False,
            "conflict_companies": [],
            "conflict_types": [],
            "severity": "none"
        }
        
        for portfolio_company in portfolio_companies:
            # Check name similarity
            if self._calculate_similarity(
                startup.company.name.lower(), 
                portfolio_company.name.lower()
            ) > 0.7:
                conflicts["has_conflicts"] = True
                conflicts["conflict_companies"].append(portfolio_company.name)
                conflicts["conflict_types"].append("name_similarity")
            
            # Check industry conflict
            if (startup.company.industry and portfolio_company.industry and
                startup.company.industry.lower() == portfolio_company.industry.lower()):
                conflicts["has_conflicts"] = True
                conflicts["conflict_companies"].append(portfolio_company.name)
                conflicts["conflict_types"].append("industry_conflict")
            
            # Check description similarity
            if (startup.company.description and portfolio_company.description and
                self._calculate_similarity(
                    startup.company.description.lower(), 
                    portfolio_company.description.lower()
                ) > 0.6):
                conflicts["has_conflicts"] = True
                conflicts["conflict_companies"].append(portfolio_company.name)
                conflicts["conflict_types"].append("business_model_conflict")
        
        # Determine severity
        if len(conflicts["conflict_companies"]) > 2:
            conflicts["severity"] = "high"
        elif len(conflicts["conflict_companies"]) > 0:
            conflicts["severity"] = "medium"
        
        return conflicts
    
    async def _calculate_portfolio_fit(self, startup: StartupProfile, vc_firm: str) -> Dict:
        """Calculate portfolio fit score."""
        portfolio_companies = await self._get_portfolio_companies(vc_firm)
        
        if not portfolio_companies:
            return {
                "portfolio_fit_score": 50.0,
                "reasoning": ["No portfolio data available"]
            }
        
        # Simple portfolio fit calculation
        portfolio_industries = [comp.industry for comp in portfolio_companies]
        industry_counts = {}
        for industry in portfolio_industries:
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        
        startup_industry = startup.company.industry
        if startup_industry not in industry_counts:
            # New industry - good fit
            portfolio_fit_score = 75.0
            reasoning = ["New industry for portfolio"]
        else:
            count = industry_counts[startup_industry]
            if count > 5:
                portfolio_fit_score = 30.0
                reasoning = [f"Industry over-represented ({count} companies)"]
            elif count > 2:
                portfolio_fit_score = 50.0
                reasoning = [f"Industry well-represented ({count} companies)"]
            else:
                portfolio_fit_score = 65.0
                reasoning = [f"Industry under-represented ({count} companies)"]
        
        return {
            "portfolio_fit_score": portfolio_fit_score,
            "reasoning": reasoning
        }
    
    async def _enhance_startups_with_websites(self, startups: List[StartupProfile]) -> List[StartupProfile]:
        """Enhance startup profiles with website information."""
        try:
            from website_finder import WebsiteFinder
            
            async with WebsiteFinder() as website_finder:
                company_names = [startup.company.name for startup in startups]
                websites = await website_finder.find_websites_batch(company_names)
                
                # Update startups with website information
                for startup in startups:
                    if startup.company.name in websites and websites[startup.company.name]:
                        startup.company.website = websites[startup.company.name]
                        logger.info(f"Enhanced {startup.company.name} with website: {startup.company.website}")
                
                return startups
        except Exception as e:
            logger.error(f"Error enhancing startups with websites: {e}")
            return startups
    
    def _create_startup_analysis(
        self,
        fit_metrics: List[FitMetrics],
        startups: List[StartupProfile],
        vc_profile: VCProfile
    ) -> List[Dict]:
        """Create detailed startup analysis."""
        startup_map = {startup.company.name: startup for startup in startups}
        
        detailed_results = []
        for metric in fit_metrics:
            startup = startup_map.get(metric.startup_id)
            if startup:
                # Robustly access overall_score and other fields
                try:
                    overall_score = getattr(metric, 'overall_score', None)
                    text_similarity = getattr(metric, 'text_similarity', None)
                    industry_alignment = getattr(metric, 'industry_alignment', None)
                    stage_alignment = getattr(metric, 'stage_alignment', None)
                    geographic_alignment = getattr(metric, 'geographic_alignment', None)
                    network_proximity = getattr(metric, 'network_proximity', None)
                except Exception:
                    # fallback for dict-like
                    overall_score = metric.get('overall_score')
                    text_similarity = metric.get('text_similarity')
                    industry_alignment = metric.get('industry_alignment')
                    stage_alignment = metric.get('stage_alignment')
                    geographic_alignment = metric.get('geographic_alignment')
                    network_proximity = metric.get('network_proximity')
                if overall_score is None:
                    continue  # skip if no score
                combined_score = (
                    overall_score * 0.4 + 
                    (startup.quality_score or 0) * 0.3 + 
                    (startup.portfolio_fit["portfolio_fit_score"] if startup.portfolio_fit else 0) * 0.3
                )
                pros, cons = self._analyze_startup_pros_cons(startup, metric, vc_profile)
                recommendation = self._get_startup_recommendation(combined_score, pros, cons)
                if startup.portfolio_conflicts and startup.portfolio_conflicts.get("has_conflicts"):
                    if startup.portfolio_conflicts.get("severity") == "high":
                        recommendation = "High Conflict - Avoid"
                    elif startup.portfolio_conflicts.get("severity") == "medium":
                        recommendation = "Moderate Conflict - Review carefully"
                result = {
                    "company_name": startup.company.name,
                    "website": startup.company.website,
                    "industry": startup.company.industry,
                    "location": startup.company.location,
                    "funding_stage": startup.company.funding_stage,
                    "product_description": startup.company.description,
                    "founders": [
                        {
                            "name": founder.name,
                            "title": founder.title,
                            "experience": founder.experience,
                            "education": founder.education,
                            "linkedin_connections": founder.linkedin_connections,
                            "endorsements": founder.endorsements,
                            "linkedin_url": founder.linkedin_url
                        }
                        for founder in startup.founders
                    ],
                    "fit_metrics": {
                        "overall_score": combined_score,
                        "fit_score": overall_score,
                        "quality_score": startup.quality_score,
                        "portfolio_fit_score": (startup.portfolio_fit["portfolio_fit_score"] if startup.portfolio_fit else None),
                        "portfolio_conflicts": startup.portfolio_conflicts,
                        "text_similarity": text_similarity,
                        "industry_alignment": industry_alignment,
                        "stage_alignment": stage_alignment,
                        "geographic_alignment": geographic_alignment,
                        "network_proximity": network_proximity
                    },
                    "recommendation": recommendation,
                    "pros": pros,
                    "cons": cons,
                    "portfolio_conflict_details": (startup.portfolio_conflicts or {}),
                    "portfolio_fit_details": (startup.portfolio_fit or {})
                }
                detailed_results.append(result)
        # Sort by combined score if present
        detailed_results.sort(key=lambda x: x["fit_metrics"].get("overall_score", 0), reverse=True)
        return detailed_results
    
    def _analyze_startup_pros_cons(
        self, 
        startup: StartupProfile, 
        metric: FitMetrics, 
        vc_profile: VCProfile
    ) -> tuple[List[str], List[str]]:
        """Analyze pros and cons of a startup."""
        pros = []
        cons = []
        
        # Analyze fit scores
        if metric.overall_score > 80:
            pros.append("Excellent fit with VC criteria")
        elif metric.overall_score > 60:
            pros.append("Good fit with VC criteria")
        else:
            cons.append("Poor fit with VC criteria")
        
        # Analyze quality
        if startup.quality_score > 80:
            pros.append("High quality founders")
        elif startup.quality_score < 50:
            cons.append("Low quality founders")
        
        # Analyze portfolio fit
        if startup.portfolio_fit["portfolio_fit_score"] > 70:
            pros.append("Good portfolio fit")
        elif startup.portfolio_fit["portfolio_fit_score"] < 40:
            cons.append("Poor portfolio fit")
        
        # Analyze conflicts
        if startup.portfolio_conflicts["has_conflicts"]:
            cons.append(f"Conflicts with {len(startup.portfolio_conflicts['conflict_companies'])} portfolio companies")
        
        return pros, cons
    
    def _get_startup_recommendation(self, score: float, pros: List[str], cons: List[str]) -> str:
        """Get recommendation based on score and analysis."""
        if score >= 80:
            return "Strong Match - Highly recommend"
        elif score >= 65:
            return "Good Match - Worth considering"
        elif score >= 50:
            return "Moderate Match - Review further"
        else:
            return "Weak Match - Low priority"
    
    async def _find_talent_for_company(
        self, 
        company, 
        max_talent: int, 
        platforms: List[str]
    ) -> List[Dict]:
        """Find talent for a specific portfolio company."""
        talent_results = []
        
        # Generate search keywords
        keywords = [company.name, company.industry]
        if company.description:
            keywords.extend(company.description.split()[:5])
        
        for platform in platforms:
            try:
                if platform == "linkedin":
                    platform_talent = await self._search_linkedin_talent(
                        company, keywords, max_talent // len(platforms)
                    )
                elif platform == "crunchbase":
                    platform_talent = await self._search_crunchbase_talent(
                        company, keywords, max_talent // len(platforms)
                    )
                elif platform == "twitter":
                    platform_talent = await self._search_twitter_talent(
                        company, keywords, max_talent // len(platforms)
                    )
                else:
                    continue
                
                talent_results.extend(platform_talent)
                    
            except Exception as e:
                logger.error(f"Error searching {platform} for {company.name}: {e}")
        
        return talent_results
    
    async def _search_linkedin_talent(self, company, keywords: List[str], max_results: int) -> List[Dict]:
        """Search LinkedIn for talent."""
        talent_results = []
        
        for keyword in keywords:
            try:
                profiles = await self.linkedin_scraper.search_people(
                    keyword, max_results=max_results // len(keywords)
                )
                
                for profile in profiles:
                    talent = {
                        "name": profile.get("name", ""),
                        "title": profile.get("title", ""),
                        "company": company.name,
                        "platform": "linkedin",
                        "profile_url": profile.get("profile_url", ""),
                        "experience": profile.get("experience", ""),
                        "location": profile.get("location", ""),
                        "match_score": 50.0,  # Base score
                        "pros": ["Professional profile"],
                        "cons": ["Limited details"]
                    }
                    talent_results.append(talent)
                    
            except Exception as e:
                logger.error(f"Error searching LinkedIn for {keyword}: {e}")
        
        return talent_results[:max_results]
    
    async def _search_crunchbase_talent(self, company, keywords: List[str], max_results: int) -> List[Dict]:
        """Search Crunchbase for talent (mock)."""
        talent_results = []
        
        mock_titles = ["CEO", "CTO", "CFO", "VP Engineering", "Head of Product"]
        mock_names = ["Alex Johnson", "Sarah Chen", "Michael Rodriguez", "Priya Patel", "David Kim"]
        
        for i in range(min(max_results, 5)):
            talent = {
                "name": mock_names[i % len(mock_names)],
                "title": mock_titles[i % len(mock_titles)],
                "company": company.name,
                "platform": "crunchbase",
                "profile_url": f"https://crunchbase.com/person/{i}",
                "experience": f"Previous experience at {company.industry} companies",
                "location": "San Francisco, CA",
                "match_score": 60.0,
                "pros": ["Senior leadership experience", "Located in major tech hub"],
                "cons": ["Limited experience details"]
            }
            talent_results.append(talent)
        
        return talent_results
    
    async def _search_twitter_talent(self, company, keywords: List[str], max_results: int) -> List[Dict]:
        """Search Twitter for talent (mock)."""
        talent_results = []
        
        mock_titles = ["Founder", "CEO", "Tech Lead", "Product Manager"]
        mock_names = ["@techfounder", "@startupceo", "@productguru", "@techleader"]
        
        for i in range(min(max_results, 4)):
            talent = {
                "name": mock_names[i % len(mock_names)],
                "title": mock_titles[i % len(mock_titles)],
                "company": company.name,
                "platform": "twitter",
                "profile_url": f"https://twitter.com/{mock_names[i][1:]}",
                "experience": f"Active in {company.industry} space",
                "location": "Global",
                "match_score": 40.0,
                "pros": ["Active in industry"],
                "cons": ["Limited professional verification", "Limited experience details"]
            }
            talent_results.append(talent)
        
        return talent_results
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio()

async def main():
    """Test the unified agent."""
    agent = UnifiedVCSourcingAgent(use_mock_data=True)
    
    # Test startup sourcing
    print("\n🚀 Testing Startup Sourcing")
    startup_results = await agent.source_startups_for_vc(
        vc_firm="Nexus Venture Partners",
        max_startups=20
    )
    
    print(f"Found {len(startup_results.results)} startups")
    for i, result in enumerate(startup_results.results[:5], 1):
        print(f"{i}. {result['startup_name']} - Score: {result['overall_score']:.1f}")
    
    # Test talent sourcing
    print("\n👥 Testing Talent Sourcing")
    talent_results = await agent.source_talent_for_portfolio(
        vc_firm="Nexus Venture Partners",
        max_talent_per_company=3
    )
    
    print(f"Found {len(talent_results.results)} talent profiles")
    for i, result in enumerate(talent_results.results[:5], 1):
        print(f"{i}. {result['name']} - {result['title']} at {result['company']}")

if __name__ == "__main__":
    asyncio.run(main()) 