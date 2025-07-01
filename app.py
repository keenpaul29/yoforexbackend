# app.py
import os
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend URL in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scalp.router, prefix="/scalp", tags=["Chart Analysis"])
app.include_router(swing.router, prefix="/swing", tags=["Chart Analysis"])
