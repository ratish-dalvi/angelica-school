#!/bin/bash

# Simple script to run the Flask webapp
echo "Letter of Recommendation Generator"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check for environment variables
if [ -z "$OPENAI_API_KEY" ] || [ -z "$OPENAI_API_BASE" ]; then
    echo ""
    echo "⚠️  WARNING: Required environment variables not set!"
    echo "Please set the following environment variables:"
    echo "export OPENAI_API_KEY='your-api-key'"
    echo "export OPENAI_API_BASE='your-api-base-url'"
    echo ""
    echo "You can add these to your ~/.bashrc or ~/.zshrc file"
    echo "or set them before running this script."
    echo ""
fi

echo ""
echo "Starting Flask application..."
echo "Open your browser to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py