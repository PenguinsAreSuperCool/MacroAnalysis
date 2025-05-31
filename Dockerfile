# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.9.6
FROM python:${PYTHON_VERSION}-slim

LABEL fly_launch_runtime="flask"

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /code

# Copy requirements and install
COPY MacroAnalysis/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Create and set permissions for data directory
RUN mkdir -p /data && chmod 777 /data

# Set environment variables for absolute database path
ENV SQLALCHEMY_DATABASE_URI=sqlite:////data/macroanalysis.db
ENV FLASK_APP=MacroAnalysis.app:app

# Create an empty database file with proper permissions
RUN touch /data/macroanalysis.db && chmod 666 /data/macroanalysis.db

# Copy the full app
COPY MacroAnalysis/ ./MacroAnalysis/
COPY README.md .
COPY .env .
# Declare volume (optional, but doesn't persist anything by itself on Fly)
VOLUME ["/data"]

# Expose port
EXPOSE 8080

# Run using the correct module path
CMD ["gunicorn", "MacroAnalysis.app:app", "--bind", "0.0.0.0:8080", "--log-level", "debug", "--capture-output"]
