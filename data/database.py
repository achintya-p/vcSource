"""
Database models and connection management.
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
import json

from utils.config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Company(Base):
    """Company database model."""
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    website = Column(String)
    industry = Column(String)
    location = Column(String)
    company_size = Column(String)
    founded_year = Column(Integer)
    funding_stage = Column(String)
    total_funding = Column(Float)
    linkedin_url = Column(String)
    crunchbase_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    founders = relationship("Founder", back_populates="company")
    fit_metrics = relationship("FitMetric", back_populates="company")

class Founder(Base):
    """Founder database model."""
    __tablename__ = "founders"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    title = Column(String)
    company_id = Column(String, ForeignKey("companies.id"))
    location = Column(String)
    experience = Column(Text)
    education = Column(Text)
    linkedin_url = Column(String)
    linkedin_connections = Column(Integer)
    endorsements = Column(Integer)
    activity_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="founders")

class VCProfile(Base):
    """VC Profile database model."""
    __tablename__ = "vc_profiles"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    website = Column(String)
    investment_thesis = Column(Text)
    focus_areas = Column(Text)  # JSON string
    investment_stages = Column(Text)  # JSON string
    portfolio_companies = Column(Text)  # JSON string
    geographic_focus = Column(Text)  # JSON string
    fund_size = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FitMetric(Base):
    """Fit metrics database model."""
    __tablename__ = "fit_metrics"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, ForeignKey("companies.id"))
    vc_firm = Column(String, nullable=False)
    overall_score = Column(Float, nullable=False)
    text_similarity = Column(Float)
    industry_alignment = Column(Float)
    stage_alignment = Column(Float)
    geographic_alignment = Column(Float)
    network_proximity = Column(Float)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="fit_metrics")

class EngagementMetric(Base):
    """Engagement metrics database model."""
    __tablename__ = "engagement_metrics"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, nullable=False)
    vc_firm = Column(String, nullable=False)
    outreach_date = Column(DateTime, nullable=False)
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    meeting_booked = Column(Boolean, default=False)
    meeting_date = Column(DateTime)
    due_diligence_started = Column(Boolean, default=False)
    investment_made = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

def save_json_field(data: list) -> str:
    """Convert list to JSON string for storage."""
    return json.dumps(data) if data else "[]"

def load_json_field(field: str) -> list:
    """Convert JSON string back to list."""
    try:
        return json.loads(field) if field else []
    except (json.JSONDecodeError, TypeError):
        return [] 