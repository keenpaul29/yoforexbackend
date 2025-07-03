from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.db import engine, Base
from routers import auth, scalp, swing

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="YoForex Chart Analysis API",
    version="1.1.0",
    description="Upload a trading chart image and get an AI-powered analysis in JSON.",
)

origins = [
    "http://localhost:3000",        # local dev
    "https://app.axiontrust.com",        # another local/dev address (no trailing slash)
    "https://axiontrust.com",   # your production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scalp.router, prefix="/scalp", tags=["Chart Analysis"])
app.include_router(swing.router, prefix="/swing", tags=["Chart Analysis"])
