"""
Optimized fit metric calculation with caching and batching.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import pickle
import hashlib
import time
from functools import lru_cache

from utils.config import get_settings
from utils.logger import get_logger
from utils.parallel_processor import CachingProcessor
from data.schemas import StartupProfile, VCProfile, FitMetrics

logger = get_logger(__name__)
settings = get_settings()

class OptimizedFitMetricCalculator:
    """Optimized fit metric calculator with caching and batching."""
    
    def __init__(self):
        self.embedding_model = None
        self.cache_processor = CachingProcessor()
        self._load_models()
        
        # Pre-computed embeddings cache
        self.embedding_cache = {}
        self.vc_embeddings = {}
    
    def _load_models(self):
        """Load models with error handling."""
        try:
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.embedding_model = None
    
    @lru_cache(maxsize=1000)
    def _get_text_embedding(self, text: str) -> np.ndarray:
        """Get cached text embedding."""
        if not text or not self.embedding_model:
            return np.zeros(384)  # Default embedding size
        
        # Create cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache first
        cached = self.cache_processor.get_cached_result(cache_key)
        if cached is not None:
            return cached
        
        # Calculate embedding
        try:
            embedding = self.embedding_model.encode([text])[0]
            self.cache_processor.cache_result(cache_key, embedding)
            return embedding
        except Exception as e:
            logger.warning(f"Error calculating embedding: {e}")
            return np.zeros(384)
    
    def calculate_fit_metrics_batch(
        self, 
        startups: List[StartupProfile], 
        vc_profile: VCProfile
    ) -> List[FitMetrics]:
        """Calculate fit metrics for multiple startups efficiently."""
        
        # Pre-compute VC embeddings once
        vc_embedding = self._get_vc_embedding(vc_profile)
        
        results = []
        for startup in startups:
            try:
                fit_metrics = self._calculate_single_fit_metrics(startup, vc_profile, vc_embedding)
                results.append(fit_metrics)
            except Exception as e:
                logger.warning(f"Error calculating fit for {startup.company.name}: {e}")
                continue
        
        return results
    
    def _get_vc_embedding(self, vc_profile: VCProfile) -> np.ndarray:
        """Get or compute VC profile embedding."""
        vc_key = f"vc_{vc_profile.name}"
        
        if vc_key in self.vc_embeddings:
            return self.vc_embeddings[vc_key]
        
        vc_text = self._prepare_vc_text(vc_profile)
        embedding = self._get_text_embedding(vc_text)
        self.vc_embeddings[vc_key] = embedding
        
        return embedding
    
    def _calculate_single_fit_metrics(
        self, 
        startup: StartupProfile, 
        vc_profile: VCProfile,
        vc_embedding: np.ndarray
    ) -> FitMetrics:
        """Calculate fit metrics for a single startup."""
        
        # Calculate individual metrics
        text_similarity = self._calculate_text_similarity_optimized(startup, vc_embedding)
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
    
    def _calculate_text_similarity_optimized(self, startup: StartupProfile, vc_embedding: np.ndarray) -> float:
        """Optimized text similarity calculation."""
        try:
            startup_text = self._prepare_startup_text(startup)
            startup_embedding = self._get_text_embedding(startup_text)
            
            # Calculate cosine similarity
            similarity = cosine_similarity([startup_embedding], [vc_embedding])[0][0]
            return float(similarity * 100)
            
        except Exception as e:
            logger.warning(f"Error calculating text similarity: {e}")
            return 0.0
    
    def _prepare_startup_text(self, startup: StartupProfile) -> str:
        """Prepare startup text efficiently."""
        text_parts = []
        
        if startup.company.description:
            text_parts.append(startup.company.description)
        
        if startup.company.industry:
            text_parts.append(startup.company.industry)
        
        # Limit founder text to avoid too long inputs
        for founder in startup.founders[:2]:  # Only first 2 founders
            if founder.experience:
                text_parts.append(founder.experience[:200])  # Limit length
            if founder.title:
                text_parts.append(founder.title)
        
        return " ".join(text_parts)
    
    def _prepare_vc_text(self, vc_profile: VCProfile) -> str:
        """Prepare VC text efficiently."""
        text_parts = []
        
        if vc_profile.investment_thesis:
            text_parts.append(vc_profile.investment_thesis)
        
        if vc_profile.focus_areas:
            text_parts.extend(vc_profile.focus_areas[:5])  # Limit to 5 focus areas
        
        if vc_profile.portfolio_companies:
            text_parts.extend(vc_profile.portfolio_companies[:10])  # Limit to 10 companies
        
        return " ".join(text_parts)
    
    def _calculate_industry_alignment(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Fast industry alignment calculation."""
        if not startup.company.industry or not vc_profile.focus_areas:
            return 0.0
        
        startup_industry = startup.company.industry.lower()
        vc_focus_areas = [area.lower() for area in vc_profile.focus_areas]
        
        # Exact match
        if startup_industry in vc_focus_areas:
            return 100.0
        
        # Quick partial match check
        for focus_area in vc_focus_areas:
            if startup_industry in focus_area or focus_area in startup_industry:
                return 75.0
        
        return 0.0
    
    def _calculate_stage_alignment(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Fast stage alignment calculation."""
        if not startup.company.funding_stage or not vc_profile.investment_stages:
            return 0.0
        
        startup_stage = startup.company.funding_stage.lower()
        vc_stages = [stage.lower() for stage in vc_profile.investment_stages]
        
        if startup_stage in vc_stages:
            return 100.0
        
        # Simple stage hierarchy
        stage_hierarchy = {'pre-seed': 1, 'seed': 2, 'series-a': 3, 'series-b': 4}
        startup_stage_num = stage_hierarchy.get(startup_stage, 0)
        
        for vc_stage in vc_stages:
            vc_stage_num = stage_hierarchy.get(vc_stage, 0)
            if abs(startup_stage_num - vc_stage_num) <= 1:
                return 75.0
        
        return 0.0
    
    def _calculate_geographic_alignment(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Fast geographic alignment calculation."""
        if not startup.company.location or not vc_profile.geographic_focus:
            return 0.0
        
        startup_location = startup.company.location.lower()
        vc_locations = [loc.lower() for loc in vc_profile.geographic_focus]
        
        if startup_location in vc_locations:
            return 100.0
        
        # Quick city/state check
        startup_parts = startup_location.split(', ')
        for part in startup_parts:
            if part in vc_locations:
                return 75.0
        
        return 0.0
    
    def _calculate_network_proximity(self, startup: StartupProfile, vc_profile: VCProfile) -> float:
        """Fast network proximity calculation."""
        if not startup.founders:
            return 0.0
        
        total_score = 0
        founder_count = len(startup.founders)
        
        for founder in startup.founders:
            founder_score = 0
            
            # Connection count (simplified scoring)
            if founder.linkedin_connections:
                if founder.linkedin_connections > 500:
                    founder_score += 30
                elif founder.linkedin_connections > 200:
                    founder_score += 20
                elif founder.linkedin_connections > 100:
                    founder_score += 10
            
            # Endorsements (simplified scoring)
            if founder.endorsements:
                if founder.endorsements > 20:
                    founder_score += 20
                elif founder.endorsements > 10:
                    founder_score += 15
            
            # Experience quality (simplified)
            if founder.experience:
                experience_score = self._evaluate_experience_fast(founder.experience)
                founder_score += experience_score
            
            total_score += founder_score
        
        return min(100.0, total_score / founder_count)
    
    def _evaluate_experience_fast(self, experience: str) -> float:
        """Fast experience evaluation."""
        score = 0
        experience_lower = experience.lower()
        
        # Quick keyword check
        relevant_keywords = ['founder', 'ceo', 'cto', 'startup', 'google', 'facebook', 'amazon']
        for keyword in relevant_keywords:
            if keyword in experience_lower:
                score += 10
        
        return min(50.0, score)
    
    def _calculate_overall_score(
        self, 
        text_similarity: float,
        industry_alignment: float,
        stage_alignment: float,
        geographic_alignment: float,
        network_proximity: float
    ) -> float:
        """Calculate overall score with optimized weights."""
        
        # Optimized weights based on importance
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
    
    def clear_cache(self):
        """Clear all caches."""
        self.cache_processor.clear_cache()
        self.embedding_cache.clear()
        self.vc_embeddings.clear()
        self._get_text_embedding.cache_clear() 