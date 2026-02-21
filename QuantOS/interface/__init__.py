import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Path Resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

def create_app():
    app = FastAPI(title="QuantOS")
    
    # 1. Initialize Templates and store in App State
    app.state.templates = Jinja2Templates(directory=TEMPLATE_DIR)
    
    # 2. Mount Static on the main APP instance
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    
    # 3. Include the Router
    from interface.server import router
    app.include_router(router)
    
    return app
