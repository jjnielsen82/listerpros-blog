#!/bin/bash
# ListerPros Blog Agent Runner
#
# This script runs the blog agent continuously.
# Set your API keys as environment variables before running.
#
# Usage:
#   chmod +x run_agent.sh
#   ./run_agent.sh
#
# Or with environment variables:
#   GROK_API_KEY="your-key" ./run_agent.sh

cd "$(dirname "$0")/.."

echo "=============================================="
echo "ListerPros Blog Agent (Grok API)"
echo "=============================================="
echo ""
echo "Starting agent at $(date)"
echo "Posts will be created every 6 hours"
echo "Press Ctrl+C to stop"
echo ""

# Check for API key
if [ -z "$GROK_API_KEY" ]; then
    echo "WARNING: GROK_API_KEY not set"
    echo "Set it with: export GROK_API_KEY='your-key'"
    echo "Get your key at: https://console.x.ai/"
    echo ""
fi

# Run the agent
python3 scripts/blog_agent.py

echo ""
echo "Agent stopped at $(date)"
