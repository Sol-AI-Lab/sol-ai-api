from pydantic import BaseModel, Field

class Query(BaseModel):
    query: str = Field(min_length=1)
