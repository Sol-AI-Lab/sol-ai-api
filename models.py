from pydantic import BaseModel, Field

class Query(BaseModel):
    query: str = Field(min_length=1)
    collection: str = Field(min_length=1)
    n_results: int = Field(min=1)

class Process(BaseModel):
    collection: str = Field(min_length=1)
    
class CleanDB(BaseModel):
    collection: str = Field(min_length=1)