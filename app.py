from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analysis

app = FastAPI(
    title="Gemini Trading Chart Analyzer",
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
app.include_router(analysis.router, prefix="/analyze", tags=["Chart Analysis"])
