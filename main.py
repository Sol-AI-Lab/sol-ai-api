from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from src.models import ProjectSearchQuery, ProjectResponse, ProjectSearchResponse
from dotenv import load_dotenv
from starlette.status import HTTP_403_FORBIDDEN
from sentence_transformers import SentenceTransformer
from src.supabase.client import supabase
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
    return response


@app.post('/search/hackathon-projects', response_model=ProjectSearchResponse, dependencies=[Depends(get_api_key)])
def search_hackathon_projects(request: ProjectSearchQuery) -> ProjectSearchResponse:
    """
    Search for hackathon projects using semantic similarity.
    Returns detailed information about matching projects.
    """
    query = request.query
    hackathon = request.hackathon.lower() if request.hackathon else "all"

    supabase_fn = {
        "renaissance": "get_similar_renaissance_projects",
        "radar": "get_similar_radar_projects",
        "breakout": "get_similar_breakout_projects"
    }.get(hackathon)

    if not supabase_fn:
        raise HTTPException(status_code=400, detail="Invalid hackathon")

    model = SentenceTransformer('all-MiniLM-L6-v2')

    embedding = model.encode(query).tolist()

    res = supabase.rpc(supabase_fn, {
        "query_embedding": embedding
    }).execute()

    formatted_results = []
    for item in res.data:
        response_data = {
            "id": item["id"],
            "project": item["project"],
            "project_link": item["project_link"],
            "description": item.get("description"),
            "country": item.get("country"),
            "additional_info": item.get("additional_info"),
            "tracks": item.get("tracks"),
            "team_members": item.get("team_members"),
            "presentation_link": item.get("presentation_link"),
            "technical_demo_link": item.get("technical_demo_link"),
            "repo_link": item.get("repo_link"),
            "hackathon": hackathon
        }
        formatted_results.append(ProjectResponse(**response_data))

    return ProjectSearchResponse(
        results=formatted_results,
        query=query
    )