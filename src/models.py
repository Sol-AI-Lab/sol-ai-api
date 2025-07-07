from pydantic import BaseModel, Field
from typing import Optional, List

class ProjectSearchQuery(BaseModel):
    query: str = Field(min_length=1, description="Search query text")
    hackathon: Optional[str] = Field(default="all", description="Hackathon to search in (renaissance, radar, breakout, or all)")
    
class ProjectResponse(BaseModel):
    id: str
    project: str
    project_link: str
    description: Optional[str] = None
    country: Optional[str] = None
    additional_info: Optional[str] = None
    tracks: Optional[str] = None
    team_members: Optional[str] = None
    presentation_link: Optional[str] = None
    repo_link: Optional[str] = None
    technical_demo_link: Optional[str] = None
    hackathon: Optional[str] = None

class ProjectSearchResponse(BaseModel):
    results: List[ProjectResponse]
    query: str