# YoForex Backend API

A comprehensive FastAPI-based backend service for forex trading analysis, chart processing, and market data. This service provides AI-powered chart analysis, price alerts, and trading tools for forex traders.

## 🌟 Features

- **AI-Powered Chart Analysis**: Upload trading charts for automated analysis
- **Real-time Market Data**: Access to forex prices and market rates
- **User Authentication**: Secure JWT-based authentication
- **Trading Community**: Forum for discussions and idea sharing
- **Price Alerts**: Set up and manage trading alerts
- **Performance Tracking**: Monitor trading performance metrics

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Redis (for rate limiting and caching)
- Google Cloud API key (for Gemini AI features)
- Twelve Data API key (for market data)

### 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/yoforexbackend.git
   cd yoforexbackend
   ```

2. **Set up virtual environment**
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

4. **Environment Configuration**
   Create a `.env` file with the following variables:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/yoforex
   
   # JWT Authentication
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   
   # External APIs
   TWELVE_API_KEY=your_twelve_data_api_key
   GEMINI_API_KEY=your_gemini_api_key
   
   # Redis
   REDIS_URL=redis://localhost:6379
   ```

5. **Database Setup**
   ```bash
   # Create database tables
   python -c "from utils.db import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

6. **Run the Application**
   ```bash
   uvicorn app:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`

## 📚 API Documentation

Access the interactive API documentation:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🔍 API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - User login (email/password)
- `POST /auth/login/request-otp` - Request OTP for phone login from Whatsapp
- `POST /auth/verify-otp` - Verify Whatsapp OTP for login
- `POST /auth/request-password-reset` - Request password reset
- `POST /auth/reset-password` - Reset password with OTP from Whatsapp
- `POST /auth/logout` - Logout user

### Chart Analysis
- `POST /scalp/chart/` - Analyze chart for scalp trading
  - Parameters: `file` (image), `timeframe` (M1, M5, M15, M30, H1)
- `GET /scalp/history` - Get scalp analysis history
- `POST /swing/chart/` - Analyze chart for swing trading
  - Parameters: `file` (image), `timeframe` (H1, D1, W1)
- `GET /swing/history` - Get swing analysis history

### Market Data
- `GET /prices/prices` - Get current forex prices
- `GET /market/quotes` - Get market quotes
- `GET /market/events` - Get market events and economic calendar
  - Parameters: `impact` (high, extreme, all), `upcoming_window` (minutes)

### Forum
- `GET /forum/categories` - Get all forum categories
- `POST /forum/categories` - Create new category (admin only)
- `GET /forum/posts` - Get forum posts with filters
  - Parameters: `category_id`, `search`, `sort_by`, `sort_order`, `page`, `per_page`
- `POST /forum/posts` - Create new forum post
- `GET /forum/posts/{post_id}` - Get post details
- `PUT /forum/posts/{post_id}` - Update post (author only)
- `DELETE /forum/posts/{post_id}` - Delete post (author only)
- `POST /forum/posts/{post_id}/comments` - Add comment to post
- `PUT /forum/comments/{comment_id}` - Update comment (author only)
- `DELETE /forum/comments/{comment_id}` - Delete comment (author only)
- `POST /forum/posts/{post_id}/like` - Like/unlike a post
- `POST /forum/comments/{comment_id}/like` - Like/unlike a comment
- `GET /forum/stats` - Get forum statistics

### Trades
- `GET /trades/` - List all trades
  - Parameters: `strategy`, `from_date`, `to_date`, `page`
- `GET /trades/{trade_id}` - Get trade details

### Performance
- `GET /performance/` - Get trading performance metrics
  - Parameters: `period` (week, month, year)

## 🛠 Project Structure

```
yoforexbackend/
├── app.py                 # Main FastAPI application
├── models.py              # SQLAlchemy models
├── requirements.txt       # Project dependencies
├── .env                  # Environment variables (gitignored)
├── .gitignore
├── README.md
├── routers/              # API route handlers
│   ├── __init__.py
│   ├── auth.py           # Authentication endpoints
│   ├── scalp.py          # Scalp trading analysis
│   ├── swing.py          # Swing trading analysis
│   ├── market.py         # Market data endpoints
│   ├── performance.py    # Performance metrics
│   ├── tools.py          # Trading tools
│   ├── trades.py         # Trade management
│   └── forum.py          # Community forum
├── schemas/              # Pydantic models
│   ├── __init__.py
│   ├── swing.py
│   └── forum.py
└── utils/                # Utility functions
    ├── __init__.py
    ├── db.py            # Database connection
    ├── security.py      # Authentication utilities
    ├── jwt.py          # JWT token handling
    └── gemini_helper.py # Gemini AI integration
```

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | Secret key for JWT tokens |
| `ALGORITHM` | No | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | 1440 | Token expiration time |
| `TWELVE_API_KEY` | No | - | API key for Twelve Data |
| `GEMINI_API_KEY` | No | - | API key for Google Gemini |
| `REDIS_URL` | No | redis://localhost:6379 | Redis connection URL |

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

