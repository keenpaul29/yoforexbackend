# YoForex Backend API

A comprehensive FastAPI-based backend service for forex trading analysis, chart processing, and market data. This service provides AI-powered chart analysis, price alerts, and trading tools for forex traders.

## 🌟 Features

- **Chart Analysis**: Upload trading charts and get AI-powered analysis
- **Market Data**: Real-time and historical forex price data
- **Price Alerts**: Set up and manage price alerts
- **Trading Tools**: Various utilities for forex traders
- **User Authentication**: Secure user management system
- **Community Features**: Share and discuss trading ideas

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Redis (for caching and background tasks)
- Google Cloud API key (for Gemini AI features)
- Twelve Data API key (for market data)

### 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/yoforexbackend.git
   cd yoforexbackend
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/yoforex
   
   # JWT Authentication
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # External APIs
   TWELVE_API_KEY=your_twelve_data_api_key
   GEMINI_API_KEY=your_gemini_api_key
   
   # Alert Configuration
   ALERTS_ENABLED=true
   ALERTS_API_URL=your_alerts_api_endpoint
   ALERT_SYNC_INTERVAL=300
   
   # Redis
   REDIS_URL=redis://localhost:6379
   ```

5. **Initialize the database**
   ```bash
   # Run database migrations
   alembic upgrade head
   
   # Or create tables directly (for development)
   python -c "from utils.db import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

6. **Run the application**
   ```bash
   uvicorn app:app --reload
   ```

   The API will be available at `http://127.0.0.1:8000`

## 📚 API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://127.0.0.1:8000/docs
- **Alternative API Docs**: http://127.0.0.1:8000/redoc

## 🔍 Available Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get access token
- `POST /auth/verify-email` - Verify email with OTP
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token

### Chart Analysis
- `POST /scalp/analyze` - Analyze a trading chart (scalp timeframe)
- `POST /swing/analyze` - Analyze a trading chart (swing timeframe)
- `GET /scalp/history` - Get analysis history
- `GET /swing/history` - Get swing analysis history

### Market Data
- `GET /prices/prices` - Get current forex prices
- `GET /market/rates` - Get market rates
- `GET /market/history` - Get historical market data

### Price Alerts
- `GET /alerts` - Get user's price alerts
- `POST /alerts` - Create a new price alert
- `PUT /alerts/{alert_id}` - Update a price alert
- `DELETE /alerts/{alert_id}` - Delete a price alert

### Community
- `GET /community/posts` - Get community posts
- `POST /community/posts` - Create a new post
- `GET /community/posts/{post_id}` - Get post details
- `POST /community/posts/{post_id}/comments` - Add comment to post

## 🛠 Development

### Project Structure
```
├── app.py                 # Main FastAPI application
├── alembic/               # Database migrations
├── models.py              # SQLAlchemy models
├── requirements.txt       # Project dependencies
├── .env                  # Environment variables (gitignored)
├── .gitignore
├── README.md
├── routers/              # API route handlers
│   ├── __init__.py
│   ├── auth.py
│   ├── scalp.py
│   ├── swing.py
│   ├── market.py
│   ├── performance.py
│   ├── tools.py
│   ├── alerts.py
│   ├── community.py
│   ├── tips.py
│   └── trades.py
├── schemas/              # Pydantic models
│   ├── __init__.py
│   └── swing.py
└── utils/                # Utility functions
    ├── __init__.py
    ├── db.py            # Database connection
    └── security.py      # Authentication utilities
```

### Running Tests
```bash
pytest tests/
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | Secret key for JWT tokens |
| `TWELVE_API_KEY` | No | API key for Twelve Data |
| `GEMINI_API_KEY` | No | API key for Google Gemini |
| `ALERTS_ENABLED` | No | Enable/disable alert syncing |
| `REDIS_URL` | No | Redis connection URL |

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

For any questions or feedback, please contact support@yoforex.com

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

