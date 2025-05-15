from fastapi import FastAPI

# this is what Uvicorn will look for
app = FastAPI()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
