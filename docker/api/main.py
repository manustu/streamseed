from fastapi import FastAPI
from .routes import auth, projects, campaigns, tests
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI(
    title="Streamseed API",
    description="This API is built to provide the backend services for the Streamseed application.",
    version="0.0.1",
    docs_url="/swagger",  # Custom path for Swagger UI
    redoc_url="/docs"  # Custom path for ReDoc UI
)

# Add middleware
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Include the routers from the auth and campaigns modules
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(campaigns.router)
app.include_router(tests.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}   
