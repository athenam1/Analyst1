#!/bin/bash

# Script to start Chrome with remote debugging enabled for LinkedIn scraping
# This allows the scraper to use your existing browser session

echo "Starting Chrome with remote debugging..."
echo "Make sure Chrome is completely closed first!"
echo ""

# Kill any existing Chrome instances
pkill -f "Google Chrome" 2>/dev/null
sleep 2

# Start Chrome with remote debugging on port 9222
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 &

echo ""
echo "Chrome started with remote debugging!"
echo "1. Log into LinkedIn in the Chrome window that opens"
echo "2. Then go to http://localhost:5001/analyst2 and start scraping"
echo ""
echo "Keep this Chrome window open while scraping."

