from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text
from src.database import Base

class Query(BaseModel):
    query: str = Field(min_length=1)
    collection: str = Field(min_length=1)
    n_results: int = Field(min=1)

class Process(BaseModel):
    collection: str = Field(min_length=1)
    
class CleanCollection(BaseModel):
    collection: str = Field(min_length=1)
    

class RenaissanceHackathonProject(Base):
    __tablename__ = "renaissance_hackathon_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project = Column(String, index=True, nullable=False)
    project_link = Column(String)
    description = Column(Text)
    country = Column(String)
    additional_info = Column(Text)
    tracks = Column(Text)
    team_members = Column(Text)
    presentation_link = Column(String)
    repo_link = Column(String)
    
class ProjectSearchQuery(BaseModel):
    query: str = Field(min_length=1, description="Search query text")
    text_column: Optional[str] = Field(default="description", description="Column to search in")
    top_n: Optional[int] = Field(default=20, description="Number of results to return")
    hackathon: Optional[str] = Field(default="all", description="Hackathon to search in (renaissance, radar, breakout, or all)")
    
class ProjectResponse(BaseModel):
    id: Optional[int] = None
    project: str
    project_link: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    additional_info: Optional[str] = None
    tracks: Optional[str] = None
    team_members: Optional[str] = None
    presentation_link: Optional[str] = None
    repo_link: Optional[str] = None
    technical_demo_link: Optional[str] = None
    similarity_score: float
    hackathon: Optional[str] = None 

class ProjectSearchResponse(BaseModel):
    results: List[ProjectResponse]
    total_results: int
    query: str
    
class RadarHackathonProject(Base):
    __tablename__ = "radar_hackathon_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project = Column(String, index=True, nullable=False)
    project_link = Column(String)
    description = Column(Text)
    country = Column(String)
    additional_info = Column(Text)
    tracks = Column(Text)
    team_members = Column(Text)
    presentation_link = Column(String)
    repo_link = Column(String)

class BreakoutHackathonProject(Base):
    __tablename__ = "breakout_hackathon_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project = Column(String, index=True, nullable=False)
    project_link = Column(String)
    description = Column(Text)
    country = Column(String)
    additional_info = Column(Text)
    tracks = Column(Text)
    team_members = Column(Text)
    presentation_link = Column(String)
    technical_demo_link = Column(String)
    repo_link = Column(String)