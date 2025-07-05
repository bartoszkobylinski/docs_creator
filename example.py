from fastapi import FastAPI

app = FastAPI()

@app.get("/ping")
def ping():
    """Simple ping."""
    return {"ping": "pong"}
