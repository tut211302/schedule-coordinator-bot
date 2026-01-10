"""
FastAPI Backend for Schedule Coordinator Bot.
Main application entry point with router registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import user, line_auth, google_auth

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="Schedule Coordinator API",
    description="Backend API for LINE Bot with Google Calendar integration",
    version="0.1.0"
)

# CORS configuration
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
# F008: User CRUD API
app.include_router(
    user.router,
    prefix="/api/users",
    tags=["users"]
)

# F011: LINE User Authentication API
app.include_router(
    line_auth.router,
    prefix="/webhook/line",
    tags=["line_auth"]
)

# F012: Google Calendar Authentication API
app.include_router(
    google_auth.router,
    prefix="/api/auth/google",
    tags=["google_auth"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Schedule Coordinator API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
