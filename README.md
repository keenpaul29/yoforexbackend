Gemini Trading Chart Analyzer

A FastAPI-based service that allows users to upload trading chart images, select a timeframe (H1, D1, W1), and receive AI-powered swing-trading analysis in JSON format using Google’s Gemini (Generative Language) API. It also includes a simple line-detection check to reject non-chart images.

Features

Image upload: Accepts PNG/JPG/GIF uploads up to 5MB.

Timeframe selection: Supports H1, D1, W1 timeframes for swing trading.

Chart detection: Uses OpenCV to verify the upload is a trading chart.

AI analysis: Sends the chart to Gemini API to get signal, confidence, entry, stop_loss, take_profit, risk_reward_ratio, detailed technical_analysis, and recommendations.

Self-test: Built-in TestClient routine for local validation.

Directory Structure

├── app.py             # Main FastAPI application
├── requirements.txt   # Python dependencies
├── .env               # Environment variables (not committed)
├── uploads/           # Temporary storage for uploaded images
└── README.md          # This file

Getting Started

Prerequisites

Python 3.8+

A valid Google Cloud API key with access to the Generative Language API (Gemini).

Installation

Clone the repository

git clone https://github.com/your-repo/chart-analyzer.git
cd chart-analyzer

Create and activate a virtual environment

python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.venv\\Scripts\\activate   # Windows

Install dependencies

pip install -r requirements.txt

Configure environment variables
Create a .env file in the project root with:

GEMINI_API_KEY=your_google_api_key_here

Running the Application

python app.py

This will:

Run the built-in self-test (if GEMINI_API_KEY is set).

Start the Uvicorn server on http://0.0.0.0:8000.

Visit http://127.0.0.1:8000/docs for the interactive Swagger UI.

API Usage

Endpoint

POST /analyze-chart/?timeframe={H1|D1|W1}

Query Parameters

timeframe (required): The chart timeframe to analyze. One of H1, D1, W1.

Form Data

file (required): The chart image file (PNG, JPG, GIF).

Response Schema

{
  "signal": "BUY or SELL",
  "confidence": 87,
  "entry": 1.0892,
  "stop_loss": 1.0850,
  "take_profit": 1.0950,
  "risk_reward_ratio": "1:1.38",
  "timeframe": "D1",
  "technical_analysis": {
    "RSI": "45.2",
    "MACD": "Bullish",
    "Moving_Average": "Above 50 EMA",
    "ICT_Order_Block": "Detected",
    "ICT_Fair_Value_Gap": "Detected",
    "ICT_Breaker_Block": "Not Detected",
    "ICT_Trendline": "Upward"
  },
  "recommendation": "...",
  "dynamic_stop_loss": 1.0850,
  "dynamic_take_profit": 1.0950
}

Example cURL

curl --location --request POST 'http://localhost:8000/analyze-chart/?timeframe=D1' \
  --header 'Accept: application/json' \
  --form 'file=@"/path/to/your/chart.png"'

Troubleshooting

Invalid file: Returns HTTP 400 with Please upload a trading chart image if the file fails the line-detection check.

AI API errors: Returns HTTP 502 if Gemini responds with an error. See logs for request/response details.

License

This project is licensed under the MIT License. See LICENSE for details.

