# RoAI Multi-LLM Platform

> Intelligent routing system for OpenAI and Google Gemini with cost optimization and full observability

## Overview

This platform automatically routes AI requests to the optimal LLM (OpenAI or Google Gemini) based on task characteristics, optimizing for cost, performance, and accuracy.

### Key Features

- **Intelligent Routing** - Automatic model selection based on task requirements
- **Ensemble Mode** - Dual-model validation for critical decisions
- **Cost Tracking** - Real-time cost monitoring and RoAI calculation
- **Observability** - Full metrics, audit logs, and analytics
- **Enterprise Controls** - Rate limiting, budget caps, caching
- **Compliance Ready** - Tamper-proof audit logs with cryptographic hash chains

## How It Works

The router selects the best model based on:

| Condition | Route To | Why |
|-----------|----------|-----|
| Requires strict JSON | OpenAI | Best structured output |
| Context > 80k tokens | Gemini | 2M token window |
| Multi-document analysis | Gemini | Superior correlation |
| Business impact > 0.8 | Ensemble | Dual validation |
| Default | OpenAI | Optimal balance |

## Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key ([Get one](https://platform.openai.com/api-keys))
- Google Gemini API key ([Get one](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone and navigate to project**
```bash
git clone <repo-url>
cd RoAI-multillm
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here

# Optional: Configure routing thresholds
CONTEXT_LENGTH_THRESHOLD=80000
BUSINESS_IMPACT_THRESHOLD=0.8

# Optional: Model selection
OPENAI_MODEL=gpt-4o-mini
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Run the Application

```bash
streamlit run app/main.py
```

The app will open at `http://localhost:8501`

## Project Structure

```
RoAI-multillm/
├── app/
│   ├── main.py                      # Streamlit UI
│   ├── router.py                    # Intelligent routing logic
│   ├── gateway.py                   # Unified LLM gateway
│   ├── advanced_gateway.py          # Caching, rate limiting, budgets
│   ├── models/
│   │   └── task.py                  # Task data model
│   ├── services/
│   │   ├── openai_service.py        # OpenAI integration
│   │   ├── gemini_service.py        # Gemini integration
│   │   ├── ensemble_service.py      # Dual-model validation
│   │   └── observability_service.py # Metrics tracking
│   ├── utils/
│   │   ├── cost_calculator.py       # Cost tracking
│   │   ├── roai_calculator.py       # ROI calculation
│   │   ├── audit_logger.py          # Tamper-proof logging
│   │   └── prompt_manager.py        # Prompt versioning
│   └── pages/
│       └── admin_dashboard.py       # Admin monitoring
├── data/
│   └── sample_risk_scenarios.json   # Test scenarios
├── tests/                           # Unit tests
├── docker-compose.yml               # Docker setup
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Usage

### Basic Risk Analysis

1. Open the web interface at `http://localhost:8501`
2. Navigate to "Risk Analysis" tab
3. Enter task details:
   - Description/prompt
   - Requires strict JSON? (checkbox)
   - Estimated context length (tokens)
   - Multi-document analysis? (checkbox)
   - Business impact (0-1 slider)
4. Click "Analyze Risk"
5. View results with routing explanation and cost breakdown

### Sample Scenarios

The app includes pre-configured test scenarios:
- Simple fraud detection → Routes to OpenAI
- Large document analysis → Routes to Gemini
- High-stakes fraud case → Routes to Ensemble

### Analytics Dashboard

View session metrics including:
- Total requests and cost
- Model distribution
- Cost savings vs. always using premium models
- RoAI (Return on AI Investment)

## Configuration

Key environment variables in `.env`:

```env
# API Keys (Required)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Model Selection
OPENAI_MODEL=gpt-4o-mini          # or gpt-4o
GEMINI_MODEL=gemini-2.0-flash-exp

# Routing Thresholds
CONTEXT_LENGTH_THRESHOLD=80000     # Tokens before switching to Gemini
BUSINESS_IMPACT_THRESHOLD=0.8      # Impact level for ensemble mode

# Enterprise Features (Optional)
ENABLE_CACHING=true
CACHE_TTL=3600                     # Cache TTL in seconds
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
DAILY_BUDGET_USD=100.0
MONTHLY_BUDGET_USD=2000.0
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_router.py

# Verbose output
pytest -v
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Manual Docker Build

```bash
# Build image
docker build -t roai-multillm .

# Run container
docker run -p 8501:8501 --env-file .env roai-multillm
```

## Architecture

### High-Level Flow

```
User Request
    ↓
Task Creation & Validation
    ↓
Intelligent Router
    ├─ OpenAI Service
    ├─ Gemini Service
    └─ Ensemble Service (both)
    ↓
AI Gateway (Unified Interface)
    ├─ OpenAI API
    └─ Gemini API
    ↓
Observability Layer
    ├─ Metrics Tracking
    ├─ Cost Calculation
    ├─ Audit Logging
    └─ RoAI Calculation
    ↓
Response to User
```

### Key Components

- **Router**: Decision engine for model selection
- **Gateway**: Unified interface abstracting provider differences
- **Services**: Provider-specific implementations (OpenAI, Gemini, Ensemble)
- **Observability**: Cross-cutting concerns (metrics, audit, cost)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

## Features

### Intelligent Routing

Routes based on task characteristics:
- JSON requirements → OpenAI (better structured output)
- Large context → Gemini (2M token window)
- Multi-document → Gemini (superior correlation)
- High impact → Ensemble (dual validation)

### Ensemble Validation

For critical decisions, runs both models in parallel:
- Compares risk scores
- Calculates confidence levels
- Escalates to human review if models disagree (>15 point difference)

### Cost Optimization

- Automatic selection of cheaper models when appropriate
- 40-60% cost reduction vs. always using premium models
- Real-time cost tracking per request and session
- RoAI calculation to prove AI value

### Enterprise Controls

- **Caching**: Response caching for repeated queries
- **Rate Limiting**: Token bucket algorithm (per minute/hour)
- **Budget Controls**: Daily and monthly spending limits
- **Audit Logging**: Cryptographic hash chain for tamper-proof logs

### Observability

- Real-time metrics dashboard
- Per-model cost breakdown
- Request/response logging
- Performance tracking (latency, tokens, success rate)

## RoAI Calculation

The platform tracks Return on AI Investment:

```
RoAI = (Fraud Prevented + Manual Cost Saved - LLM Cost) / LLM Cost
```

Example:
- LLM Cost: $100/month
- Fraud Prevented: $50,000/month
- Manual Cost Saved: $2,000/month
- **RoAI = 519x** (Every $1 spent returns $519 in value)

## Troubleshooting

### Common Issues

**ModuleNotFoundError**
```bash
pip install -r requirements.txt
```

**API Key Not Found**
- Ensure `.env` file exists in project root
- Check `OPENAI_API_KEY` and `GEMINI_API_KEY` are set

**Rate Limit Exceeded**
- Adjust limits in `.env`: `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_PER_HOUR`
- Wait for rate limit reset

**Windows Path Issues**
- Ensure `data/` directory exists
- Use forward slashes in paths

**Port Already in Use**
```bash
streamlit run app/main.py --server.port 8502
```

## Development

### Adding a New LLM Provider

1. Create service: `app/services/your_provider_service.py`
2. Add gateway methods: `app/gateway.py`
3. Update router: `app/router.py`
4. Update cost calculator: `app/utils/cost_calculator.py`
5. Add tests: `tests/test_your_provider.py`

### Running in Development Mode

```bash
streamlit run app/main.py --server.runOnSave true
```

## Roadmap

- [ ] Claude (Anthropic) integration
- [ ] REST API layer
- [ ] Redis caching for distributed deployments
- [ ] Real-time alerts (Slack, Email)
- [ ] Machine learning-based routing
- [ ] Multi-tenant support

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request


## Support

For questions or issues:
- Open an issue on GitHub
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for detailed docs
- Review test files in `tests/` for usage examples

---

**Built with**: OpenAI GPT-4o-mini, Google Gemini 2.0 Flash, Streamlit, Python
