#!/bin/bash
# Script to start Chrome with remote debugging enabled on port 9222
# This allows the worker to connect to an existing Chrome instance

echo "Starting Chrome with remote debugging on port 9222..."
echo ""

# macOS Chrome path (modify if needed)
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Check if Chrome exists
if [ ! -f "$CHROME_PATH" ]; then
    echo "Chrome not found at: $CHROME_PATH"
    echo "Please edit this script and set CHROME_PATH to your Chrome executable path."
    exit 1
fi

# Start Chrome with remote debugging
"$CHROME_PATH" --remote-debugging-port=9222 --user-data-dir="$HOME/Library/Application Support/Google/Chrome" &

echo ""
echo "Chrome started with remote debugging enabled!"
echo "Port: 9222"
echo ""
echo "You can now run the worker script."
echo ""
