from fastapi import FastAPI
app = FastAPI()

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "1.0.0"}
