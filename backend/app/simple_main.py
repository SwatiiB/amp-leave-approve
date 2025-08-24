from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.db import db, users_collection, leaves_collection

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Backend is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
