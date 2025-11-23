# Dockerfile for Explainable AI Climate-CVD Project
# Python 3.11 base with all dependencies for model training, API, and dashboard

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for geopandas and spatial libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data_raw data_synthetic data_processed outputs notebooks

# Generate synthetic data on build
RUN python data_synthetic/generate_synthetic.py --seed 42

# Preprocess data
RUN python src/preprocess.py --input data_synthetic/region_daily.csv --output data_processed/region_daily.parquet

# Train models (commented out for faster builds - uncomment for production)
# RUN python src/models/xgb_train.py && \
#     python src/explainers.py && \
#     python src/models/run_dlnm.py && \
#     python src/models/produce_policy_statement.py && \
#     python src/viz.py

# Expose ports
# 8000 for FastAPI
# 8501 for Streamlit
EXPOSE 8000 8501

# Default command runs API
# Override with docker run command to run dashboard or other services
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Example commands:
# Build: docker build -t explainable-ai-cvd .
# Run API: docker run -p 8000:8000 explainable-ai-cvd
# Run Dashboard: docker run -p 8501:8501 explainable-ai-cvd streamlit run src/dashboard/app.py --server.port=8501 --server.address=0.0.0.0
