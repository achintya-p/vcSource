"""
FastAPI application for the VC Sourcing Agent.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn

from utils.config import get_settings
from utils.logger import get_logger
from data.schemas import SearchCriteria, SourcingResult, VCProfile, StartupProfile
from main import VCSourcingAgent

app = FastAPI(
    title="VC Sourcing Agent API",
    description="API for sourcing early-stage startups for VC firms",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger(__name__)
settings = get_settings()

# Global agent instance
agent = None

def get_agent():
    """Get or create the VC sourcing agent."""
    global agent
    if agent is None:
        agent = VCSourcingAgent()
    return agent

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    logger.info("Starting VC Sourcing Agent API")
    get_agent()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global agent
    if agent:
        agent.close()
        logger.info("VC Sourcing Agent API shutdown complete")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "VC Sourcing Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/source", response_model=SourcingResult)
async def source_startups(
    vc_firm: str,
    stages: Optional[List[str]] = None,
    industries: Optional[List[str]] = None,
    locations: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    max_results: int = 100,
    agent: VCSourcingAgent = Depends(get_agent)
):
    """Source startups for a VC firm."""
    try:
        result = agent.source_startups(
            vc_firm=vc_firm,
            stages=stages,
            industries=industries,
            locations=locations,
            keywords=keywords,
            max_results=max_results
        )
        return result
    except Exception as e:
        logger.error(f"Error sourcing startups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vc-profile/{vc_firm}", response_model=VCProfile)
async def get_vc_profile(
    vc_firm: str,
    agent: VCSourcingAgent = Depends(get_agent)
):
    """Get VC firm profile."""
    try:
        from scrapers.vc_profile_scraper import VCProfileScraper
        scraper = VCProfileScraper()
        profile = scraper.scrape_vc_profile(vc_firm)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"VC firm {vc_firm} not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting VC profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-fit")
async def calculate_fit_metrics(
    startup: StartupProfile,
    vc_firm: str,
    agent: VCSourcingAgent = Depends(get_agent)
):
    """Calculate fit metrics for a startup and VC firm."""
    try:
        # Get VC profile
        from scrapers.vc_profile_scraper import VCProfileScraper
        scraper = VCProfileScraper()
        vc_profile = scraper.scrape_vc_profile(vc_firm)
        
        if not vc_profile:
            raise HTTPException(status_code=404, detail=f"VC firm {vc_firm} not found")
        
        # Calculate fit metrics
        fit_metrics = agent.fit_calculator.calculate_fit_metrics(startup, vc_profile)
        
        return fit_metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating fit metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-quality")
async def calculate_quality_score(
    startup: StartupProfile,
    agent: VCSourcingAgent = Depends(get_agent)
):
    """Calculate quality score for a startup."""
    try:
        quality_score = agent.quality_scorer.calculate_quality_score(startup)
        breakdown = agent.quality_scorer.get_quality_breakdown(startup)
        
        return {
            "quality_score": quality_score,
            "breakdown": breakdown
        }
    except Exception as e:
        logger.error(f"Error calculating quality score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics():
    """Get analytics and performance metrics."""
    # This would typically query the database for analytics
    return {
        "total_startups_sourced": 0,
        "average_fit_score": 0.0,
        "average_quality_score": 0.0,
        "top_industries": [],
        "top_locations": []
    }

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 