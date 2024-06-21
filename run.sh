#!/bin/bash

# Path to your project directory
PROJECT_DIR=$(pwd)

# Command to start npm
NPM_START_CMD="cd $PROJECT_DIR && npm start"

# Command to run scrapper.py with the latest Python interpreter
SCRAPPER_CMD="cd $PROJECT_DIR && python3 scrapper.py"

# Open a new terminal window and run npm start
osascript <<EOF
tell application "Terminal"
    do script "$NPM_START_CMD"
end tell
EOF

# Open another new terminal window and run scrapper.py
osascript <<EOF
tell application "Terminal"
    do script "$SCRAPPER_CMD"
end tell
EOF
