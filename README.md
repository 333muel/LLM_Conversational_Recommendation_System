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

1.  **Clone the project**: 
    ```bash
    git clone https://github.com/333muel/FYP_Conversational_Recommendation_System
    ```
2.  **Download Data**: Download the latest version of zip file from [this link](https://drive.google.com/drive/folders/14jOhTDdqM-RTZ_LnWHunLiAWLhpMRef3?usp=share_link) and place the 2 folders extracted `checkpoints` and `data` in the root directory.
3. **Start Ollama Server**: Download Ollama from the [official website](https://ollama.com/download) and download the qwen3:latest model
    ```bash
    # After downloading ollama
    ollama pull qwen3:latest
    ```
4. **Pull Mongodb Server**:
    ```bash
    docker pull mongo:8.0
    ```
4.  **Start Services**:
    ```bash
    docker-compose up -d --build
    ```
5.  **Initialize Database** (run once):
    ```bash
    docker-compose exec backend python scripts/initialize_db.py
    ```

Once running:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **MongoDB**: localhost:27018 (using `recommendation_demo_db`)

### 2. Managing the Service

Once the initial setup is complete, use these commands to manage the system:

**To Start the system**:
```bash
docker-compose up -d
```

**To Stop the system** (keeps data preserved in volumes):
```bash
docker-compose stop
```

**To Restart after stopping**:
```bash
docker-compose start
```

**To Shut Down completely** (stops containers but keeps database data):
```bash
docker-compose down
```

**To View Logs** (useful for debugging):
```bash
# View all logs
docker-compose logs -f

# View only backend logs
docker-compose logs -f backend
```

**To Clear Everything and Start Fresh** (Warning: deletes database data):
```bash
docker-compose down -v
```

## Performance Results

The system supports multiple recommendation algorithms. Comprehensive performance comparisons can be found in `docs/performance.txt`.

Top Performers (Recall@10):
1. **SGL** (2021) - Test Recall: 0.0322
2. **LightGCN** (2020) - Test Recall: 0.0303
3. **DMF** (2017) - Test Recall: 0.0252
