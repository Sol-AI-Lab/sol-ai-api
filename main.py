from fastapi import FastAPI

app = FastAPI()

@app.get("/ping")
async def read_root():
    return "pong!"