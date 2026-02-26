# AI Recommendation Agent

An AI-powered recommendation system using LangGraph, RecBole, FastAPI, and Ollama.

## Features

- **LangGraph Workflow**: Orchestrates the recommendation process
- **RecBole Integration**: Uses trained LightGCN model for recommendations
- **Ollama LLM**: Generates natural language responses using qwen3:latest
- **MongoDB**: Stores product information and mappings
- **FastAPI**: RESTful API for recommendation requests

## Project Structure

```
ai-chain/
├── app.py                     # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── apps/                      # Main application modules
    ├── config/                # Configuration management
    ├── core/                  # Core business logic
    │   ├── domain/           # Domain layer (MVC pattern)
    │   ├── llm/              # Large Language Model integration
    │   └── agent/            # AI agent functionality
    ├── database/             # Data persistence layer
    └── common/               # Shared utilities
```

## Setup

1. **Create and activate virtual environment** (recommended):
```bash
# Create virtual environment (Recommend python 3.12 for dependency stability)
python3.12 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Or use the convenience script:
./activate.sh
```

2. **Install dependencies**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Ensure MongoDB is running**:
```bash
# MongoDB should be running on localhost:27017
```

5. **Populate MongoDB with product data**:
```bash
python scripts/populate_products.py --csv-path ../cleaned_basic.csv
```

6. **Ensure Ollama is running with qwen3:latest**:
```bash
# Install Ollama and pull the model
ollama pull qwen3:latest
```

6. **Ensure RecBole dataset and model checkpoint are in place**:
   - Dataset: `recbole_atomic_amazon_200k/` directory
   - Model checkpoint: `LightGCN-Nov-05-2025_01-25-48.pth` in root

## Running the Application

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST `/api/conversation/recommend`

Get product recommendations based on user message.

**Request Body**:
```json
{
  "message": "I'm looking for hair accessories",
  "user_id": "optional_user_id",
  "top_k": 10,
  "model": "qwen3:latest",
  "algorithm": "LightGCN"
}
```

**Parameters:**
- `message` (required): User's query message
- `user_id` (optional): User ID (uses demo user if not provided)
- `top_k` (optional): Number of recommendations to return (1-50, default: 10)
- `model` (optional): LLM model to use (default: qwen3:latest)
- `algorithm` (optional): RecBole algorithm/checkpoint name (e.g., 'LightGCN', 'BPR'). If not found, defaults to LightGCN

**Response**:
```json
{
  "response": "AI-generated recommendation text...",
  "recommendations": [
    {
      "item_id": "B09W2NRFH2",
      "title": "Product Title",
      "description": "Product description",
      "rating": 4.5,
      "price": "$8.99",
      "categories": "Beauty & Personal Care",
      "score": 0.95,
      "rank": 1
    }
  ],
  "user_id": "AFNT6ZJCYQN3WDIKUSWHJDXNND2Q",
  "success": true,
  "debug": {
    "raw_recommendations_count": 20,
    "product_details_count": 10,
    "has_final_response": true,
    "algorithm_used": "LightGCN",
    "model_used": "qwen3:latest"
  }
}
```

#### GET `/api/algorithms/available`

Get list of available algorithms based on checkpoint files.

**Response:**
```json
{
  "algorithms": ["LightGCN", "BPR"],
  "count": 2
}
```

### GET `/health`

Health check endpoint.

### GET `/`

Root endpoint with API information.

## Usage Examples

### Basic Request
```bash
curl -X POST http://localhost:8000/api/conversation/recommend \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me beauty products"}'
```

### Custom Parameters
```bash
# Custom top_k and algorithm
curl -X POST http://localhost:8000/api/conversation/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me beauty products",
    "top_k": 5,
    "algorithm": "LightGCN"
  }'

# List available algorithms
curl http://localhost:8000/api/algorithms/available
```

## Workflow

1. User sends a message via API (with optional `top_k`, `model`, `algorithm` parameters)
2. **RecommendItem Node**: 
   - Finds checkpoint matching the `algorithm` parameter (or defaults to LightGCN)
   - Uses RecBole model to generate recommendations
   - Returns `context_k` items for LLM context
3. **GenerateResponse Node**: 
   - Fetches product details from MongoDB
   - Uses Ollama (with specified `model` or default) to generate natural language response
   - Focuses on top `top_k` items but uses all context items for better understanding
4. Returns formatted response with top `top_k` recommendations

## Algorithm Selection

The system automatically finds checkpoints by algorithm name:
- Checkpoints are named: `{AlgorithmName}-{timestamp}.pth` (e.g., `LightGCN-Nov-09-2025_21-24-15.pth`)
- If the specified algorithm is not found, it falls back to LightGCN
- Use `/api/algorithms/available` to see all available algorithms

## Notes

- Uses a demo user ID from the dataset by default
- Product mappings are stored in MongoDB
- The RecBole model checkpoint must match the dataset format
- Multiple algorithm engines are cached for performance

