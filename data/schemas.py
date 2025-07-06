"""
Data schemas for the VC Sourcing Agent.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class CompanyProfile(BaseModel):
    """Schema for company information."""
    name: str
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    funding_stage: Optional[str] = None
    total_funding: Optional[float] = None
    linkedin_url: Optional[HttpUrl] = None
    crunchbase_url: Optional[HttpUrl] = None

class FounderProfile(BaseModel):
    """Schema for founder information."""
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    linkedin_connections: Optional[int] = None
    endorsements: Optional[int] = None
    activity_score: Optional[float] = None

class VCProfile(BaseModel):
    """Schema for VC firm information."""
    name: str
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None
    investment_thesis: Optional[str] = None
    focus_areas: List[str] = Field(default_factory=list)
    investment_stages: List[str] = Field(default_factory=list)
    portfolio_companies: List[str] = Field(default_factory=list)
    geographic_focus: List[str] = Field(default_factory=list)
    fund_size: Optional[str] = None  # Changed from float to str to handle "$35B+" format

class StartupProfile(BaseModel):
    """Schema for startup information."""
    company: CompanyProfile
    founders: List[FounderProfile] = Field(default_factory=list)
    fit_score: Optional[float] = None
    quality_score: Optional[float] = None
    market_score: Optional[float] = None
    portfolio_conflicts: Optional[Dict[str, Any]] = None
    portfolio_fit: Optional[Dict[str, Any]] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    source: str = "linkedin"

class FitMetrics(BaseModel):
    """Schema for fit calculation results."""
    startup_id: str
    vc_firm: str
    overall_score: float = Field(ge=0, le=100)
    text_similarity: float = Field(ge=0, le=100)
    industry_alignment: float = Field(ge=0, le=100)
    stage_alignment: float = Field(ge=0, le=100)
    geographic_alignment: float = Field(ge=0, le=100)
    network_proximity: float = Field(ge=0, le=100)
    calculated_at: datetime = Field(default_factory=datetime.now)

class EngagementMetrics(BaseModel):
    """Schema for tracking engagement."""
    startup_id: str
    vc_firm: str
    outreach_date: datetime
    response_received: bool = False
    response_date: Optional[datetime] = None
    meeting_booked: bool = False
    meeting_date: Optional[datetime] = None
    due_diligence_started: bool = False
    investment_made: bool = False
    notes: Optional[str] = None

class SearchCriteria(BaseModel):
    """Schema for search parameters."""
    vc_firm: str
    stages: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    company_size_min: Optional[int] = None
    company_size_max: Optional[int] = None
    founded_after: Optional[int] = None
    max_results: int = 100

class SourcingResult(BaseModel):
    """Schema for sourcing results."""
    search_criteria: SearchCriteria
    startups: List[StartupProfile]
    total_found: int
    processing_time: float
    scraped_at: datetime = Field(default_factory=datetime.now) 