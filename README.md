# AI Recommendation Agent System

This is a full-stack AI-powered recommendation system that integrates graph-based and sequential recommendation models (via RecBole) with Large Language Models (via Ollama/LangGraph) and a modern web interface (Next.js/Shadcn).

## Project Structure

- `backend/`: FastAPI server that orchestrates the AI workflow using LangGraph.
- `frontend/`: Next.js web application for browsing products and interacting with the AI agent.
- `data/`: Contains the Amazon Reviews dataset (atomic files) and processed product metadata.
- `checkpoints/`: Trained model checkpoints for various recommendation algorithms (LightGCN, SGL, etc.).
- `docs/`: Performance analysis and evaluation results.

## Quick Start

### 1. Run the system using Docker

This is the recommended way to run the full stack (MongoDB, Backend, and Frontend).

1.  **Download Data**: Download the `data` folder from the provided link and place it in the project root.
2.  **Start Services**:
    ```bash
    docker-compose up -d --build
    ```
3.  **Initialize Database** (run once):
    ```bash
    docker-compose exec backend python scripts/initialize_db.py
    ```

Once running:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **MongoDB**: localhost:27018 (using `recommendation_demo_db`)

## Performance Results

The system supports multiple recommendation algorithms. Comprehensive performance comparisons can be found in `docs/performance.txt`.

Top Performers (Recall@10):
1. **SGL** (2021) - Test Recall: 0.0322
2. **LightGCN** (2020) - Test Recall: 0.0303
3. **DMF** (2017) - Test Recall: 0.0252
