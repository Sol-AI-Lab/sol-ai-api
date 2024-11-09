from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from models import Query, Process, CleanDB
from vector_db import query_collection, process_files_from_directory, clean_collection

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
    data = Query.model_validate(request.model_dump())
    
    query = data.query
    collection = data.collection
    n_results = data.n_results
    
    results = query_collection(query, collection, n_results).get("documents")[0]
    
    response = {
        "content": results
    }
    return JSONResponse(status_code=200, content=response)

@app.post('/process', response_model=dict, status_code=200)
def process(request: Process) -> dict:
    data = Process.model_validate(request.model_dump())
    collection = data.collection
    
    process_files_from_directory(f"./context/{collection}", collection)

    response = {'success': True, "message": "documents successfully processed!"}
    return JSONResponse(status_code=200, content=response)

@app.post('/clean-collection', response_model=dict, status_code=200)
def clean(request: CleanDB) -> dict:
    data = CleanDB.model_validate(request.model_dump())
    collection = data.collection
    
    clean_collection(collection)
    
    response = {'success': True, "message": "Local DB successfully cleaned!"}
    return JSONResponse(status_code=200, content=response)