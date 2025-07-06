"""
Fit metric calculation for startup-VC matching.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestRegressor
from sentence_transformers import SentenceTransformer
import pickle
import re

from utils.config import get_settings
from utils.logger import get_logger
from data.schemas import StartupProfile, VCProfile, FitMetrics, SearchCriteria

logger = get_logger(__name__)
settings = get_settings()

class FitMetricCalculator:
    """Calculate fit metrics between startups and VC firms."""
    
    def __init__(self):
        self.embedding_model = None
        self.tfidf_vectorizer = None
        self.fit_model = None
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models."""
        try:
            # Load sentence transformer for embeddings
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
            
            # Load TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Try to load pre-trained fit model
            try:
                with open(settings.FIT_MODEL_PATH, 'rb') as f:
                    self.fit_model = pickle.load(f)
                logger.info("Loaded pre-trained fit model")
            except FileNotFoundError:
                logger.info("No pre-trained fit model found, will use rule-based scoring")
                self.fit_model = None
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def calculate_fit_metrics(
        self, 
        startup: StartupProfile, 
        vc_profile: VCProfile
    ) -> FitMetrics:
        """Calculate comprehensive fit metrics between startup and VC."""
        
        # Calculate individual metrics
        text_similarity = self._calculate_text_similarity(startup, vc_profile)
        industry_alignment = self._calculate_industry_alignment(startup, vc_profile)
        stage_alignment = self._calculate_stage_alignment(startup, vc_profile)
        geographic_alignment = self._calculate_geographic_alignment(startup, vc_profile)
        network_proximity = self._calculate_network_proximity(startup, vc_profile)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            text_similarity, industry_alignment, stage_alignment, 
            geographic_alignment, network_proximity
        )
        
        return FitMetrics(
            startup_id=startup.company.name,
            vc_firm=vc_profile.name,
            overall_score=overall_score,
            text_similarity=text_similarity,
            industry_alignment=industry_alignment,
            stage_alignment=stage_alignment,
            geographic_alignment=geographic_alignment,
            network_proximity=network_proximity
        )
    
    def _calculate_text_similarity(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Calculate text similarity between startup and VC profile."""
        try:
            # Prepare startup text
            startup_text = self._prepare_startup_text(startup)
            
            # Prepare VC text
            vc_text = self._prepare_vc_text(vc_profile)
            
            if not startup_text or not vc_text:
                return 0.0
            
            # Calculate embeddings
            startup_embedding = self.embedding_model.encode([startup_text])[0]
            vc_embedding = self.embedding_model.encode([vc_text])[0]
            
            # Calculate cosine similarity
            similarity = cosine_similarity(
                [startup_embedding], 
                [vc_embedding]
            )[0][0]
            
            # Convert to percentage (0-100)
            return float(similarity * 100)
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0
    
    def _prepare_startup_text(self, startup: StartupProfile) -> str:
        """Prepare startup text for similarity calculation."""
        text_parts = []
        
        # Company description
        if startup.company.description:
            text_parts.append(startup.company.description)
        
        # Industry
        if startup.company.industry:
            text_parts.append(startup.company.industry)
        
        # Founder information
        for founder in startup.founders:
            if founder.experience:
                text_parts.append(founder.experience)
            if founder.title:
                text_parts.append(founder.title)
        
        return " ".join(text_parts)
    
    def _prepare_vc_text(self, vc_profile: VCProfile) -> str:
        """Prepare VC profile text for similarity calculation."""
        text_parts = []
        
        # Investment thesis
        if vc_profile.investment_thesis:
            text_parts.append(vc_profile.investment_thesis)
        
        # Focus areas
        if vc_profile.focus_areas:
            text_parts.extend(vc_profile.focus_areas)
        
        # Portfolio companies (as context)
        if vc_profile.portfolio_companies:
            text_parts.extend(vc_profile.portfolio_companies)
        
        return " ".join(text_parts)
    
    def _calculate_industry_alignment(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Calculate industry alignment score."""
        try:
            if not startup.company.industry or not vc_profile.focus_areas:
                return 0.0
            
            startup_industry = startup.company.industry.lower()
            vc_focus_areas = [area.lower() for area in vc_profile.focus_areas]
            
            # Check for exact matches
            if startup_industry in vc_focus_areas:
                return 100.0
            
            # Check for partial matches
            for focus_area in vc_focus_areas:
                if (startup_industry in focus_area or 
                    focus_area in startup_industry or
                    self._calculate_word_similarity(startup_industry, focus_area) > 0.7):
                    return 75.0
            
            # Check for related industries
            related_industries = self._get_related_industries(startup_industry)
            for related in related_industries:
                if related in vc_focus_areas:
                    return 50.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating industry alignment: {e}")
            return 0.0
    
    def _calculate_stage_alignment(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Calculate funding stage alignment."""
        try:
            if not startup.company.funding_stage or not vc_profile.investment_stages:
                return 0.0
            
            startup_stage = startup.company.funding_stage.lower()
            vc_stages = [stage.lower() for stage in vc_profile.investment_stages]
            
            # Exact match
            if startup_stage in vc_stages:
                return 100.0
            
            # Stage hierarchy for partial matches
            stage_hierarchy = {
                'pre-seed': 1,
                'seed': 2,
                'series-a': 3,
                'series-b': 4,
                'series-c': 5,
                'growth': 6
            }
            
            startup_stage_num = stage_hierarchy.get(startup_stage, 0)
            
            for vc_stage in vc_stages:
                vc_stage_num = stage_hierarchy.get(vc_stage, 0)
                
                # VC invests in this stage or adjacent stages
                if abs(startup_stage_num - vc_stage_num) <= 1:
                    return 75.0
                elif abs(startup_stage_num - vc_stage_num) <= 2:
                    return 50.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating stage alignment: {e}")
            return 0.0
    
    def _calculate_geographic_alignment(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Calculate geographic alignment score."""
        try:
            if not startup.company.location or not vc_profile.geographic_focus:
                return 0.0
            
            startup_location = startup.company.location.lower()
            vc_locations = [loc.lower() for loc in vc_profile.geographic_focus]
            
            # Exact match
            if startup_location in vc_locations:
                return 100.0
            
            # Check for city/state matches
            startup_parts = startup_location.split(', ')
            for part in startup_parts:
                if part in vc_locations:
                    return 75.0
            
            # Check for region matches
            startup_region = self._get_region(startup_location)
            for vc_loc in vc_locations:
                vc_region = self._get_region(vc_loc)
                if startup_region == vc_region:
                    return 50.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating geographic alignment: {e}")
            return 0.0
    
    def _calculate_network_proximity(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Calculate network proximity score."""
        try:
            total_score = 0
            founder_count = len(startup.founders)
            
            if founder_count == 0:
                return 0.0
            
            for founder in startup.founders:
                founder_score = 0
                
                # Connection count score (0-30 points)
                if founder.linkedin_connections:
                    if founder.linkedin_connections > 1000:
                        founder_score += 30
                    elif founder.linkedin_connections > 500:
                        founder_score += 20
                    elif founder.linkedin_connections > 200:
                        founder_score += 10
                
                # Endorsements score (0-20 points)
                if founder.endorsements:
                    if founder.endorsements > 50:
                        founder_score += 20
                    elif founder.endorsements > 20:
                        founder_score += 15
                    elif founder.endorsements > 10:
                        founder_score += 10
                
                # Experience quality score (0-50 points)
                if founder.experience:
                    experience_score = self._evaluate_experience_quality(founder.experience)
                    founder_score += experience_score
                
                total_score += founder_score
            
            # Average score per founder
            return min(100.0, total_score / founder_count)
            
        except Exception as e:
            logger.error(f"Error calculating network proximity: {e}")
            return 0.0
    
    def _calculate_overall_score(
        self, 
        text_similarity: float,
        industry_alignment: float,
        stage_alignment: float,
        geographic_alignment: float,
        network_proximity: float
    ) -> float:
        """Calculate overall fit score using weighted average."""
        
        # Weights for different metrics
        weights = {
            'text_similarity': 0.25,
            'industry_alignment': 0.25,
            'stage_alignment': 0.20,
            'geographic_alignment': 0.15,
            'network_proximity': 0.15
        }
        
        overall_score = (
            text_similarity * weights['text_similarity'] +
            industry_alignment * weights['industry_alignment'] +
            stage_alignment * weights['stage_alignment'] +
            geographic_alignment * weights['geographic_alignment'] +
            network_proximity * weights['network_proximity']
        )
        
        return round(overall_score, 2)
    
    def _calculate_word_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words."""
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, word1, word2).ratio()
        except:
            return 0.0
    
    def _get_related_industries(self, industry: str) -> List[str]:
        """Get related industries for matching."""
        industry_mapping = {
            'fintech': ['financial services', 'banking', 'payments', 'insurtech'],
            'healthtech': ['healthcare', 'medical', 'biotech', 'digital health'],
            'e-commerce': ['retail', 'marketplace', 'online shopping'],
            'saas': ['software', 'enterprise', 'b2b', 'cloud'],
            'ai/ml': ['artificial intelligence', 'machine learning', 'data science'],
            'mobile': ['mobile app', 'ios', 'android', 'mobile gaming']
        }
        
        return industry_mapping.get(industry, [])
    
    def _get_region(self, location: str) -> str:
        """Get region from location."""
        location_lower = location.lower()
        
        if any(city in location_lower for city in ['san francisco', 'palo alto', 'mountain view']):
            return 'bay area'
        elif any(city in location_lower for city in ['new york', 'brooklyn', 'manhattan']):
            return 'new york'
        elif any(city in location_lower for city in ['austin', 'dallas', 'houston']):
            return 'texas'
        elif any(city in location_lower for city in ['boston', 'cambridge']):
            return 'boston'
        else:
            return 'other'
    
    def _evaluate_experience_quality(self, experience: str) -> float:
        """Evaluate the quality of founder experience."""
        score = 0
        
        # Check for relevant experience keywords
        relevant_keywords = [
            'founder', 'ceo', 'cto', 'co-founder', 'startup', 'entrepreneur',
            'google', 'facebook', 'amazon', 'apple', 'microsoft', 'netflix',
            'uber', 'airbnb', 'stripe', 'square', 'palantir'
        ]
        
        experience_lower = experience.lower()
        for keyword in relevant_keywords:
            if keyword in experience_lower:
                score += 10
        
        return min(50.0, score)
    
    def train_fit_model(self, training_data: List[Tuple[StartupProfile, VCProfile, float]]):
        """Train a machine learning model for fit prediction."""
        try:
            # Prepare training features
            X = []
            y = []
            
            for startup, vc, target_score in training_data:
                features = self._extract_features(startup, vc)
                X.append(features)
                y.append(target_score)
            
            # Train Random Forest model
            self.fit_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.fit_model.fit(X, y)
            
            # Save the model
            with open(settings.FIT_MODEL_PATH, 'wb') as f:
                pickle.dump(self.fit_model, f)
            
            logger.info("Fit model trained and saved successfully")
            
        except Exception as e:
            logger.error(f"Error training fit model: {e}")
    
    def _extract_features(self, startup: StartupProfile, vc_profile: VCProfile) -> List[float]:
        """Extract features for ML model training."""
        features = []
        
        # Basic metrics
        text_sim = self._calculate_text_similarity(startup, vc_profile)
        industry_align = self._calculate_industry_alignment(startup, vc_profile)
        stage_align = self._calculate_stage_alignment(startup, vc_profile)
        geo_align = self._calculate_geographic_alignment(startup, vc_profile)
        network_prox = self._calculate_network_proximity(startup, vc_profile)
        
        features.extend([text_sim, industry_align, stage_align, geo_align, network_prox])
        
        # Additional features
        features.append(len(startup.founders))
        features.append(len(startup.company.description) if startup.company.description else 0)
        features.append(len(vc_profile.focus_areas))
        features.append(len(vc_profile.portfolio_companies))
        
        return features 