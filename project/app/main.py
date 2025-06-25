from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, items

app = FastAPI(
    title="Advanced FastAPI Example",
    description="An example project demonstrating routers, dependencies, and models.",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
tags_metadata = [
    {"name": "users", "description": "Operations on users."},
    {"name": "items", "description": "Operations on items."},
]
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(items.router, prefix="/items", tags=["items"])