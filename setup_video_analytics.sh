#!/bin/bash
# Setup script for Video Analytics dependencies

echo "Setting up Video Analytics dependencies..."
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  No virtual environment detected."
    echo "   It's recommended to use a virtual environment."
    echo "   You can create one with: python3 -m venv venv"
    echo "   Then activate it: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies
echo "Installing opencv-python and numpy..."
python3 -m pip install opencv-python numpy

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Dependencies installed successfully!"
    echo ""
    echo "You can now run the test script:"
    echo "  python3 test_video_analytics.py"
else
    echo ""
    echo "❌ Installation failed. Try:"
    echo "  1. Use a virtual environment"
    echo "  2. Run: python3 -m pip install --user opencv-python numpy"
    echo "  3. Or use sudo (not recommended): sudo pip3 install opencv-python numpy"
fi
