#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH to project root
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "🐍 Virtual environment activated"
echo "🔧 PYTHONPATH set to: $PYTHONPATH"
echo "📁 Current directory: $(pwd)"
echo ""
echo "Now you can run:"
echo "  python QA/bridge_domain_validator.py --iterations 10"
echo "  python QA/advanced_bridge_domain_tester.py"
echo ""
echo "Or use the convenience script:"
echo "  ./run_qa.sh validator --iterations 10"
echo "  ./run_qa.sh advanced" 