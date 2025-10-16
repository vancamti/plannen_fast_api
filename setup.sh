#!/bin/bash
# Setup script for initial project configuration
# Note: This script is designed for Unix-like systems (Linux, macOS).
# For Windows, use WSL or manually follow the README installation steps.

set -e

echo "🚀 Setting up Plannen FastAPI..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created. Please update it with your configuration."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update the .env file with your configuration"
echo "2. Start PostgreSQL and Elasticsearch: docker-compose up -d"
echo "3. Run database migrations: alembic upgrade head"
echo "4. Start the application: ./run.sh or uvicorn app.main:app --reload"
