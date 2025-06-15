from fastapi import FastAPI, Security, HTTPException, Depends, Query as QueryParam
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from src.database import get_db
from src.models import BreakoutHackathonProject, ProjectSearchQuery, ProjectResponse, ProjectSearchResponse, RadarHackathonProject, RenaissanceHackathonProject
from src.hackathons import search_projects, create_tables, import_all_hackathon_data
from dotenv import load_dotenv
from starlette.status import HTTP_403_FORBIDDEN
import os
load_dotenv()

app = FastAPI()
app.title = "Sol AI API"
app.version = "0.1.0"

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEY = os.getenv('API_KEY')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No API Key provided"
        )
    if api_key_header != API_KEY:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate API Key"
        )
    return api_key_header

@app.get("/ping", response_model=dict, status_code=200)
def ping() -> dict:
    response = { "message": "pong!" }
    return JSONResponse(status_code=200, content=response)


@app.post('/search/hackathon-projects', response_model=ProjectSearchResponse, dependencies=[Depends(get_api_key)])
def search_hackathon_projects(request: ProjectSearchQuery) -> ProjectSearchResponse:
    """
    Search for hackathon projects using semantic similarity.
    
    Returns detailed information about matching projects.
    """
    create_tables()
    
    query = request.query
    text_column = request.text_column
    top_n = request.top_n
    hackathon = request.hackathon if hasattr(request, 'hackathon') else "all"
    
    results = search_projects(query, text_column, top_n, use_db=True, hackathon=hackathon)
    
    formatted_results = []
    for item in results:
        project = item["project"]
        score = item["similarity_score"]
        hackathon_source = item.get("hackathon", "unknown")
        
        response_data = {
            "id": project.id,
            "project": project.project,
            "project_link": project.project_link,
            "description": project.description,
            "country": project.country,
            "additional_info": project.additional_info,
            "tracks": project.tracks,
            "team_members": project.team_members,
            "presentation_link": project.presentation_link,
            "repo_link": project.repo_link,
            "similarity_score": float(score),
            "hackathon": hackathon_source
        }
        
        if hackathon_source == "breakout" and hasattr(project, "technical_demo_link"):
            response_data["technical_demo_link"] = project.technical_demo_link
        
        formatted_results.append(ProjectResponse(**response_data))
    
    response = ProjectSearchResponse(
        results=formatted_results,
        total_results=len(formatted_results),
        query=query
    )
    
    return response

@app.get('/admin/import-hackathon-data', dependencies=[Depends(get_api_key)])
def import_hackathon_data():
    """
    Import data from all hackathon Excel files into the database.
    """
    try:
        import_all_hackathon_data()
        return {"message": "Hackathon data imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing hackathon data: {str(e)}")
    
@app.get('/hackathon/{hackathon_name}/projects', dependencies=[Depends(get_api_key)])
def get_hackathon_projects(
    hackathon_name: str,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all projects from a specific hackathon.
    """
    db = get_db()
    try:
        if hackathon_name.lower() == "renaissance":
            model_class = RenaissanceHackathonProject
        elif hackathon_name.lower() == "radar":
            model_class = RadarHackathonProject
        elif hackathon_name.lower() == "breakout":
            model_class = BreakoutHackathonProject
        else:
            raise HTTPException(status_code=400, detail=f"Unknown hackathon: {hackathon_name}")
        
        projects = db.query(model_class).offset(skip).limit(limit).all()
        
        formatted_projects = []
        for project in projects:
            project_data = {
                "id": project.id,
                "project": project.project,
                "project_link": project.project_link,
                "description": project.description,
                "country": project.country,
                "additional_info": project.additional_info,
                "tracks": project.tracks,
                "team_members": project.team_members,
                "presentation_link": project.presentation_link,
                "repo_link": project.repo_link,
                "hackathon": hackathon_name
            }
            
            if hackathon_name.lower() == "breakout" and hasattr(project, "technical_demo_link"):
                project_data["technical_demo_link"] = project.technical_demo_link
                
            formatted_projects.append(project_data)
        
        return {
            "hackathon": hackathon_name,
            "projects": formatted_projects,
            "total": len(formatted_projects)
        }
    
    finally:
        db.close()