#!/bin/bash
# Setup script to add weekly prompt update cron job
# This script should be run once to set up the cron job

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_CMD=$(which python3 || which python)

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

FETCH_SCRIPT="$PROJECT_ROOT/scripts/fetch_prompts_from_internet.py"
CRON_LOG="$PROJECT_ROOT/logs/prompt_fetch.log"
CRON_ERROR_LOG="$PROJECT_ROOT/logs/prompt_fetch_error.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Create cron job entry (runs every Monday at 2 AM)
CRON_ENTRY="0 2 * * 1 cd $PROJECT_ROOT && $PYTHON_CMD $FETCH_SCRIPT >> $CRON_LOG 2>> $CRON_ERROR_LOG"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "fetch_prompts_from_internet.py"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "fetch_prompts_from_internet.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✓ Cron job added successfully!"
echo ""
echo "Cron job details:"
echo "  Schedule: Every Monday at 2:00 AM"
echo "  Script: $FETCH_SCRIPT"
echo "  Log: $CRON_LOG"
echo "  Error log: $CRON_ERROR_LOG"
echo ""
echo "To view your crontab: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"

