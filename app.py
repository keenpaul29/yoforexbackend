from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import swing
from routers import scalp

app = FastAPI(
    title="YoForex Chart Analysis API FastAPI",
    description="Upload a trading chart image and get an AI-powered analysis in JSON.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Register the chart-analysis router
app.include_router(swing.router, prefix="/swing", tags=["Chart Analysis"])
app.include_router(scalp.router, prefix="/scalp", tags=["Chart Analysis"])
