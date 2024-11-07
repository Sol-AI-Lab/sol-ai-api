from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from models import Query
from vector_db import query_collection, process_files_from_directory, clean_local_db

app = FastAPI()
app.title = "Sol AI API"
app.version = "0.1.0"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping", response_model=dict, status_code=200)
def ping() -> dict:
    response = { "message": "pong!" }
    return JSONResponse(status_code=200, content=response)

@app.post("/query", response_model=dict, status_code=200)
def query(request: Query) -> dict:
    query = Query.model_validate(request.model_dump()).query
    results = query_collection(query).get("documents")
    response = {
        "content": results
    }
    return JSONResponse(status_code=200, content=response)

@app.get('/process', response_model=dict, status_code=200)
def process() -> dict:

    process_files_from_directory("./solana_docs")

    response = {'success': True, "message": "documents successfully processed!"}
    return JSONResponse(status_code=200, content=response)

@app.get('/clean-local-db', response_model=dict, status_code=200)
def clean() -> dict:
    clean_local_db()
    
    response = {'success': True, "message": "Local DB successfully cleaned!"}
    return JSONResponse(status_code=200, content=response)