from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="mail-janitor")


@app.get("/up")
def healthcheck():
    return JSONResponse({"status": "ok"})


@app.get("/")
def root():
    return JSONResponse({"app": "mail-janitor", "status": "booting"})
