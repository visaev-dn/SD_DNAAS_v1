#!/bin/bash

# Set PYTHONPATH to project root
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "🔧 PYTHONPATH set to: $PYTHONPATH"
echo "📁 Current directory: $(pwd)"
echo ""

# Check if script argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: ./run_qa.sh <script_name> [arguments...]"
    echo ""
    echo "Available scripts:"
    echo "  validator     - Run bridge domain validator"
    echo "  advanced      - Run advanced bridge domain tester"
    echo ""
    echo "Examples:"
    echo "  ./run_qa.sh validator --iterations 20"
    echo "  ./run_qa.sh advanced"
    echo "  ./run_qa.sh advanced --random-iterations 15 --stress-iterations 30"
    echo ""
    echo "Advanced tester options:"
    echo "  --random-iterations N      Number of random pair tests (default: 10)"
    echo "  --same-leaf-iterations N   Number of same-leaf tests (default: 5)"
    echo "  --stress-iterations N      Number of stress tests (default: 20)"
    echo "  --failed-spine-limit N     Maximum failed spine tests (default: 5)"
    exit 1
fi

SCRIPT_NAME=$1
shift  # Remove first argument, keep the rest

case $SCRIPT_NAME in
    "validator")
        echo "🚀 Running bridge domain validator..."
        python QA/bridge_domain_validator.py "$@"
        ;;
    "advanced")
        echo "🚀 Running advanced bridge domain tester..."
        python QA/advanced_bridge_domain_tester.py "$@"
        ;;
    *)
        echo "❌ Unknown script: $SCRIPT_NAME"
        echo "Available scripts: validator, advanced"
        exit 1
        ;;
esac 