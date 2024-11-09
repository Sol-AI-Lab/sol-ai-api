from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from models import Query, Process, CleanCollection
from vector_db import query_collection, process_files_from_directory, clean_collection
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

@app.post("/query", response_model=dict, status_code=200, dependencies=[Depends(get_api_key)])
def query(request: Query) -> dict:
    data = Query.model_validate(request.model_dump())
    
    query = data.query
    collection = data.collection
    n_results = data.n_results
    
    results = query_collection(query, collection, n_results).get("documents")[0]
    
    response = {
        "content": results
    }
    return JSONResponse(status_code=200, content=response)

@app.post('/process', response_model=dict, status_code=200, dependencies=[Depends(get_api_key)])
def process(request: Process) -> dict:
    data = Process.model_validate(request.model_dump())
    collection = data.collection
    
    process_files_from_directory(f"./context/{collection}", collection)

    response = {'success': True, "message": "documents successfully processed!"}
    return JSONResponse(status_code=200, content=response)

@app.post('/clean-collection', response_model=dict, status_code=200, dependencies=[Depends(get_api_key)])
def clean(request: CleanCollection) -> dict:
    data = CleanCollection.model_validate(request.model_dump())
    collection = data.collection
    
    clean_collection(collection)
    
    response = {'success': True, "message": "Local DB successfully cleaned!"}
    return JSONResponse(status_code=200, content=response)