#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Zerostic RAG System Setup ==="

# 1. Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv) using python3..."
    python3 -m venv .venv
else
    echo "Virtual environment (.venv) already exists."
fi

# 2. Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# 3. Upgrade pip and install dependencies
echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements from requirements.txt..."
# We can use uv to speed up if available, but pip is extremely robust.
pip install -r requirements.txt

# 4. Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "Created .env. PLEASE open .env and put your actual OpenRouter API key!"
else
    echo ".env file already exists."
fi

echo "=== Setup Completed Successfully! ==="
echo "To run the RAG system, first activate the environment with: source .venv/bin/activate"
