# Stage 1: Build the React frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve using Python FastAPI backend
FROM python:3.9-slim
WORKDIR /app

# Install build dependencies (pulp, pandas, etc. may need it for compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy official processed datasets and backend script
COPY backend/ ./backend
COPY data/processed/ ./data/processed

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Expose FastAPI server port
EXPOSE 8000

# Set Python output buffering
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "backend/main.py"]
