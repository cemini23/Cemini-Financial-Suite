from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router as api_router
from app.core.config import settings

import asyncio
from app.core.database import init_db
from modules.satoshi_vision.harvester import Harvester
from modules.execution.autopilot import CeminiAutopilot

app = FastAPI(
    title="Kalshi by Cemini",
    description="Automated Trading & Prediction Engine | Cemini Financial Suite",
    version="2.0.8"
)

@app.on_event("startup")
async def startup_event():
    try:
        # 1. Initialize Data Vault (SQLite)
        await init_db()
        
        # 2. Launch Harvester Daemon (Background Task)
        harvester = Harvester()
        asyncio.create_task(harvester.run())

        # 3. Launch Autopilot (Background Task)
        autopilot = CeminiAutopilot()
        asyncio.create_task(autopilot.run())
        
        print("[*] Startup: Success (Harvester + Autopilot Online)")
    except Exception as e:
        print(f"[!] Startup CRASH: {e}")

# Include our routes
app.include_router(api_router, prefix="/api/v1")

# Mount the 'frontend' folder to serve static files (css, js)
# We use this to serve app.js and any other assets
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve the Dashboard at the root URL
@app.get("/")
async def read_index():
    return FileResponse('frontend/index.html')

if __name__ == "__main__":
    import uvicorn
    # Enforced fixed port for Suite Protocol
    # Changed host to 0.0.0.0 for Docker compatibility
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
