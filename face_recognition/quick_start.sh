#!/bin/bash
# Quick Start Script for Face Recognition Attendance System

echo "=================================================="
echo "Face Recognition Attendance System - Quick Start"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed or not in PATH"
    echo "Please install Python 3.10 and try again"
    exit 1
fi

echo "✅ Python found: $(python --version)"
echo ""

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ Error: pip is not installed"
    exit 1
fi

echo "✅ pip found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Error installing dependencies"
    exit 1
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1️⃣  Start the Flask server:"
echo "   python app.py"
echo ""
echo "2️⃣  Register students (in a new terminal):"
echo "   python register.py"
echo ""
echo "3️⃣  Start face recognition (in a new terminal):"
echo "   python main.py"
echo ""
echo "4️⃣  Open dashboard in browser:"
echo "   http://127.0.0.1:5000"
echo ""
echo "=================================================="
