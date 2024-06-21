#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
OS=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"

# Install Homebrew if on macOS and not installed
if [ "$OS" == "mac" ]; then
    if ! command_exists brew; then
        echo "Homebrew is not installed, installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> /Users/$(whoami)/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo "Homebrew is already installed."
    fi
fi

# Install Node.js if not present or incorrect version
if command_exists node; then
    NODE_VERSION=$(node -v | grep -oE '[0-9]+' | head -n 1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo "Node.js version is less than 18, installing Node.js 18..."
        if [ "$OS" == "linux" ]; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif [ "$OS" == "mac" ]; then
            brew install node@18
            brew link --force --overwrite node@18
        fi
    else
        echo "Node.js 18 or higher is already installed."
    fi
else
    echo "Node.js is not installed, installing Node.js 18..."
    if [ "$OS" == "linux" ]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif [ "$OS" == "mac" ]; then
        brew install node@18
        brew link --force --overwrite node@18
    fi
fi

# Install Python if not present
if ! command_exists python3; then
    echo "Python is not installed, installing Python..."
    if [ "$OS" == "linux" ]; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    elif [ "$OS" == "mac" ]; then
        brew install python
    fi
else
    echo "Python is already installed."
fi

# Install requirements from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    python3 -m pip install -r requirements.txt
else
    echo "requirements.txt not found, skipping Python packages installation."
fi

# Install Node.js packages
if [ -f "package.json" ]; then
    echo "Installing Node.js packages from package.json..."
    npm install
else
    echo "package.json not found, skipping Node.js packages installation."
fi

echo "Setup completed successfully!"
