from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
from routers import auth_router, staff, swings, overrides, flights, agent
import os

app = FastAPI(title="ISSG Roster App", version="1.0.0")

# Init DB tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# API routers
app.include_router(auth_router.router)
app.include_router(staff.router)
app.include_router(swings.router)
app.include_router(overrides.router)
app.include_router(flights.router)
app.include_router(agent.router)

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}
