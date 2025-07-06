"""
Quality scoring for founders and startups.
"""
from typing import List, Dict, Optional
import re

from utils.config import get_settings
from utils.logger import get_logger
from data.schemas import StartupProfile, FounderProfile

logger = get_logger(__name__)
settings = get_settings()

class QualityScorer:
    """Score the quality of founders and startups."""
    
    def __init__(self):
        # Prestigious companies for experience scoring
        self.prestigious_companies = {
            'google', 'facebook', 'meta', 'amazon', 'apple', 'microsoft', 'netflix',
            'uber', 'airbnb', 'stripe', 'square', 'palantir', 'tesla', 'spacex',
            'linkedin', 'twitter', 'snapchat', 'instagram', 'whatsapp', 'zoom',
            'salesforce', 'oracle', 'adobe', 'intel', 'nvidia', 'amd', 'cisco',
            'goldman sachs', 'mckinsey', 'bain', 'bcg', 'deloitte', 'pwc'
        }
        
        # Prestigious universities for education scoring
        self.prestigious_universities = {
            'stanford', 'harvard', 'mit', 'berkeley', 'caltech', 'princeton',
            'yale', 'columbia', 'upenn', 'cornell', 'brown', 'dartmouth',
            'duke', 'northwestern', 'chicago', 'nyu', 'usc', 'ucla', 'ucsd',
            'oxford', 'cambridge', 'imperial', 'lse', 'eth zurich', 'tsinghua'
        }
        
        # Prestigious honors and awards (with point values)
        self.prestigious_honors = {
            # Academic honors
            'rhodes scholar': 25,
            'marshall scholar': 25,
            'fulbright scholar': 20,
            'gates cambridge': 20,
            'truman scholar': 18,
            'goldwater scholar': 15,
            'churchill scholar': 20,
            'mitchell scholar': 18,
            'schwarzman scholar': 20,
            'knight-hennessy': 25,
            'neuroscience scholar': 15,
            'neo scholar': 20,
            
            # Startup accelerators and fellowships
            'y combinator': 30,
            'y combinator alumni': 25,
            'techstars': 15,
            '500 startups': 12,
            'startup chile': 10,
            'masschallenge': 8,
            'founder institute': 5,
            
            # Prestigious fellowships
            'rise fellow': 25,
            'kleiner perkins fellow': 25,
            'kp fellow': 25,
            'greylock fellow': 25,
            'sequoia scout': 20,
            'first round fellow': 20,
            'andreessen horowitz scout': 20,
            'a16z scout': 20,
            'thiel fellow': 30,
            'thiel fellowship': 30,
            'forbes 30 under 30': 20,
            'fortune 40 under 40': 18,
            'inc 30 under 30': 15,
            
            # Industry awards
            'turing award': 50,
            'nobel prize': 50,
            'macarthur fellow': 35,
            'macarthur genius': 35,
            'sloan fellow': 25,
            'packard fellow': 25,
            'guggenheim fellow': 20,
            'national science foundation': 15,
            'nsf graduate fellow': 15,
            'nsf postdoc': 12,
            
            # Competition wins
            'google science fair': 15,
            'intel isef': 12,
            'regeneron sts': 15,
            'davidson fellow': 15,
            'google code-in': 8,
            'google summer of code': 8,
            'facebook hackathon': 5,
            'microsoft imagine cup': 8,
            
            # Military and government
            'west point': 20,
            'naval academy': 20,
            'air force academy': 20,
            'coast guard academy': 18,
            'merchant marine academy': 15,
            'white house fellow': 25,
            'presidential innovation fellow': 20,
            
            # Corporate programs
            'google apm': 20,
            'google associate product manager': 20,
            'facebook rotpm': 18,
            'facebook rotational product manager': 18,
            'microsoft pm': 15,
            'amazon pm': 15,
            'apple pm': 15,
            'uber pm': 12,
            'airbnb pm': 12,
            
            # Research and publications
            'nature': 20,
            'science': 20,
            'cell': 18,
            'neuron': 15,
            'pnas': 12,
            'jama': 15,
            'lancet': 15,
            'ieee': 10,
            'acm': 10,
            'arxiv': 8,
            
            # Patents
            'patent': 10,
            'patents': 10,
            'patented': 10,
            'inventor': 12,
            'co-inventor': 8
        }
        
        # Relevant job titles for founder quality
        self.founder_titles = {
            'founder', 'co-founder', 'ceo', 'cto', 'cpo', 'cmo', 'cfo',
            'president', 'chief executive', 'chief technology', 'chief product',
            'chief marketing', 'chief financial', 'chief operating', 'chief data',
            'chief revenue', 'chief growth', 'chief strategy', 'chief innovation'
        }
    
    def calculate_quality_score(self, startup: StartupProfile) -> float:
        """Calculate overall quality score for a startup."""
        try:
            if not startup.founders:
                return 0.0
            
            # Calculate founder quality scores
            founder_scores = []
            for founder in startup.founders:
                founder_score = self._calculate_founder_quality(founder)
                founder_scores.append(founder_score)
            
            # Calculate company quality score
            company_score = self._calculate_company_quality(startup.company)
            
            # Calculate team completeness score
            team_score = self._calculate_team_completeness(startup.founders)
            
            # Weighted average: 60% founders, 25% company, 15% team
            overall_score = (
                (sum(founder_scores) / len(founder_scores)) * 0.6 +
                company_score * 0.25 +
                team_score * 0.15
            )
            
            return round(overall_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def _calculate_founder_quality(self, founder: FounderProfile) -> float:
        """Calculate quality score for a founder."""
        try:
            total_score = 0
            
            # Experience quality (0-35 points)
            experience_score = self._evaluate_experience(founder.experience)
            total_score += experience_score
            
            # Education quality (0-20 points)
            education_score = self._evaluate_education(founder.education)
            total_score += education_score
            
            # Prestigious honors (0-30 points)
            honors_score = self._evaluate_honors(founder)
            total_score += honors_score
            
            # Network strength (0-15 points)
            network_score = self._evaluate_network(founder)
            total_score += network_score
            
            return min(100.0, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating founder quality: {e}")
            return 0.0
    
    def _evaluate_honors(self, founder: FounderProfile) -> float:
        """Evaluate prestigious honors and awards."""
        score = 0
        
        # Check experience for honors
        if founder.experience:
            experience_lower = founder.experience.lower()
            for honor, points in self.prestigious_honors.items():
                if honor in experience_lower:
                    score += points
        
        # Check education for honors
        if founder.education:
            education_lower = founder.education.lower()
            for honor, points in self.prestigious_honors.items():
                if honor in education_lower:
                    score += points
        
        # Check name for specific patterns (like "Dr." for PhDs)
        if founder.name and 'dr.' in founder.name.lower():
            score += 10
        
        return min(30.0, score)
    
    def _evaluate_experience(self, experience: Optional[str]) -> float:
        """Evaluate the quality of founder experience."""
        if not experience:
            return 0.0
        
        score = 0
        experience_lower = experience.lower()
        
        # Check for prestigious companies
        for company in self.prestigious_companies:
            if company in experience_lower:
                score += 12
        
        # Check for relevant experience keywords
        relevant_keywords = [
            'founder', 'ceo', 'cto', 'co-founder', 'startup', 'entrepreneur',
            'director', 'manager', 'lead', 'senior', 'principal', 'architect',
            'vp', 'vice president', 'head of', 'chief', 'executive'
        ]
        
        for keyword in relevant_keywords:
            if keyword in experience_lower:
                score += 3
        
        # Check for years of experience (rough estimate)
        if 'years' in experience_lower or 'yr' in experience_lower:
            # Look for number patterns that might indicate years
            year_patterns = re.findall(r'(\d+)\s*(?:years?|yrs?)', experience_lower)
            if year_patterns:
                years = max([int(y) for y in year_patterns])
                if years >= 10:
                    score += 15
                elif years >= 5:
                    score += 12
                elif years >= 3:
                    score += 8
                elif years >= 1:
                    score += 4
        
        return min(35.0, score)
    
    def _evaluate_education(self, education: Optional[str]) -> float:
        """Evaluate the quality of founder education."""
        if not education:
            return 0.0
        
        score = 0
        education_lower = education.lower()
        
        # Check for prestigious universities
        for university in self.prestigious_universities:
            if university in education_lower:
                score += 12
        
        # Check for advanced degrees
        advanced_degrees = ['phd', 'doctorate', 'mba', 'master', 'm.s.', 'm.a.', 'md']
        for degree in advanced_degrees:
            if degree in education_lower:
                score += 8
        
        # Check for relevant fields
        relevant_fields = [
            'computer science', 'engineering', 'business', 'economics',
            'mathematics', 'physics', 'chemistry', 'biology', 'medicine',
            'data science', 'statistics', 'finance', 'marketing'
        ]
        
        for field in relevant_fields:
            if field in education_lower:
                score += 3
        
        return min(20.0, score)
    
    def _evaluate_network(self, founder: FounderProfile) -> float:
        """Evaluate founder's network strength."""
        score = 0
        
        # LinkedIn connections
        if founder.linkedin_connections:
            if founder.linkedin_connections > 1000:
                score += 10
            elif founder.linkedin_connections > 500:
                score += 8
            elif founder.linkedin_connections > 200:
                score += 6
            elif founder.linkedin_connections > 100:
                score += 4
        
        # Endorsements
        if founder.endorsements:
            if founder.endorsements > 50:
                score += 5
            elif founder.endorsements > 20:
                score += 4
            elif founder.endorsements > 10:
                score += 3
        
        return min(15.0, score)
    
    def _evaluate_title(self, title: Optional[str]) -> float:
        """Evaluate the relevance of founder's title."""
        if not title:
            return 0.0
        
        title_lower = title.lower()
        
        # Check for founder/executive titles
        for founder_title in self.founder_titles:
            if founder_title in title_lower:
                return 15.0
        
        # Check for other relevant titles
        relevant_titles = [
            'director', 'manager', 'lead', 'senior', 'principal',
            'architect', 'engineer', 'scientist', 'researcher'
        ]
        
        for title_keyword in relevant_titles:
            if title_keyword in title_lower:
                return 8.0
        
        return 0.0
    
    def _calculate_company_quality(self, company) -> float:
        """Calculate quality score for the company."""
        try:
            score = 0
            
            # Company description quality
            if company.description:
                desc_length = len(company.description)
                if desc_length > 200:
                    score += 20
                elif desc_length > 100:
                    score += 15
                elif desc_length > 50:
                    score += 10
            
            # Industry relevance
            if company.industry:
                relevant_industries = [
                    'fintech', 'healthtech', 'ai', 'ml', 'saas', 'e-commerce',
                    'marketplace', 'mobile', 'software', 'technology'
                ]
                
                industry_lower = company.industry.lower()
                for relevant in relevant_industries:
                    if relevant in industry_lower:
                        score += 15
                        break
            
            # Location quality
            if company.location:
                top_locations = [
                    'san francisco', 'new york', 'austin', 'boston',
                    'seattle', 'los angeles', 'chicago', 'miami'
                ]
                
                location_lower = company.location.lower()
                for location in top_locations:
                    if location in location_lower:
                        score += 10
                        break
            
            # Company age (if available)
            if company.founded_year:
                current_year = 2024  # This should be dynamic
                age = current_year - company.founded_year
                if age <= 3:  # Early-stage is good
                    score += 15
                elif age <= 5:
                    score += 10
                elif age <= 10:
                    score += 5
            
            return min(100.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating company quality: {e}")
            return 0.0
    
    def _calculate_team_completeness(self, founders: List[FounderProfile]) -> float:
        """Calculate team completeness score."""
        try:
            score = 0
            
            # Number of founders
            founder_count = len(founders)
            if founder_count >= 3:
                score += 30
            elif founder_count == 2:
                score += 25
            elif founder_count == 1:
                score += 15
            
            # Role diversity
            roles = set()
            for founder in founders:
                if founder.title:
                    title_lower = founder.title.lower()
                    if 'ceo' in title_lower or 'founder' in title_lower:
                        roles.add('ceo')
                    elif 'cto' in title_lower or 'tech' in title_lower:
                        roles.add('cto')
                    elif 'cpo' in title_lower or 'product' in title_lower:
                        roles.add('cpo')
                    elif 'cmo' in title_lower or 'marketing' in title_lower:
                        roles.add('cmo')
                    elif 'cfo' in title_lower or 'finance' in title_lower:
                        roles.add('cfo')
            
            # Score based on role diversity
            if len(roles) >= 3:
                score += 40
            elif len(roles) == 2:
                score += 30
            elif len(roles) == 1:
                score += 20
            
            # Check for key roles
            key_roles = {'ceo', 'cto', 'cpo'}
            if key_roles.issubset(roles):
                score += 30
            elif len(key_roles.intersection(roles)) >= 2:
                score += 20
            elif len(key_roles.intersection(roles)) >= 1:
                score += 10
            
            return min(100.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating team completeness: {e}")
            return 0.0
    
    def get_quality_breakdown(self, startup: StartupProfile) -> Dict:
        """Get detailed breakdown of quality scores."""
        try:
            breakdown = {
                'overall_score': self.calculate_quality_score(startup),
                'founders': [],
                'company_score': self._calculate_company_quality(startup.company),
                'team_completeness': self._calculate_team_completeness(startup.founders)
            }
            
            for founder in startup.founders:
                founder_breakdown = {
                    'name': founder.name,
                    'overall_score': self._calculate_founder_quality(founder),
                    'experience_score': self._evaluate_experience(founder.experience),
                    'education_score': self._evaluate_education(founder.education),
                    'network_score': self._evaluate_network(founder),
                    'title_score': self._evaluate_title(founder.title)
                }
                breakdown['founders'].append(founder_breakdown)
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Error getting quality breakdown: {e}")
            return {'overall_score': 0.0} 