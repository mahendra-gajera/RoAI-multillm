#!/bin/bash

# Multi-LLM Risk Intelligence Platform - Setup Script

echo "🧠 Multi-LLM Risk Intelligence Platform Setup"
echo "============================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo "✅ pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - GOOGLE_API_KEY"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

echo "============================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run: streamlit run app/main.py"
echo "3. Visit: http://localhost:8501"
echo ""
echo "For Docker deployment:"
echo "  docker-compose up --build"
echo ""
echo "============================================="
