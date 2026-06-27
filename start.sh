#!/bin/bash

# Clear output log files if they exist
rm -f backend/backend.log backend/mlflow.log frontend/frontend.log

echo "=========================================================="
echo "    STARTING CV-ATS OPTIMIZATION ENGINE SERVICES"
echo "=========================================================="

# 1. Start Backend FastAPI
echo "[1/3] Starting FastAPI Backend on http://localhost:8000..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 2. Start MLflow UI
echo "[2/3] Starting MLflow UI on http://localhost:5050..."
cd backend
source venv/bin/activate
mlflow ui --backend-store-uri file:$(pwd)/../ml/mlruns --port 5050 > mlflow.log 2>&1 &
MLFLOW_PID=$!
cd ..

# 3. Start Frontend Next.js
echo "[3/3] Starting Next.js Frontend on http://localhost:3000..."
cd frontend
yarn dev > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "=========================================================="
echo "✔ All services launched successfully!"
echo "----------------------------------------------------------"
echo "🔗 Frontend       : http://localhost:3000"
echo "🔗 Backend Docs   : http://localhost:8000/docs"
echo "🔗 MLflow Tracker : http://localhost:5050"
echo "----------------------------------------------------------"
echo "📝 Logs captured at: "
echo "   - backend/backend.log"
echo "   - backend/mlflow.log"
echo "   - frontend/frontend.log"
echo "=========================================================="
echo "Press Ctrl+C to terminate all services."

# Trap Ctrl+C and kill background processes
cleanup() {
    echo -e "\n\nShutting down all services..."
    echo "Stopping Backend (PID $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    echo "Stopping MLflow (PID $MLFLOW_PID)..."
    kill $MLFLOW_PID 2>/dev/null
    echo "Stopping Frontend (PID $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    echo "Done. All services stopped."
    exit
}

trap cleanup INT

# Wait for background jobs to finish
wait
