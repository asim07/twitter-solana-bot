#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print and execute a command, recording any errors
execute_command() {
    echo "Executing: $@"
    "$@"
    if [ $? -ne 0 ]; then
        echo "Error executing: $@" >> errors.log
    fi
}

# Clear previous errors log
> errors.log

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
            execute_command curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            execute_command sudo apt-get install -y nodejs
        elif [ "$OS" == "mac" ]; then
            execute_command brew install node@18
            echo "Changing permissions on /usr/local/include/node..."
            sudo chown -R $(whoami) /usr/local/include/node
            sudo chmod -R u+w /usr/local/include/node
            execute_command brew link --force --overwrite node@18
            if [ $? -ne 0 ]; then
                echo "Attempting to change permissions on /usr/local/share/doc/node..."
                sudo chown -R $(whoami) /usr/local/share/doc/node
                sudo chmod -R u+w /usr/local/share/doc/node
                execute_command brew link --force --overwrite node@18
            fi
        fi
    else
        echo "Node.js 18 or higher is already installed."
    fi
else
    echo "Node.js is not installed, installing Node.js 18..."
    if [ "$OS" == "linux" ]; then
        execute_command curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        execute_command sudo apt-get install -y nodejs
    elif [ "$OS" == "mac" ]; then
        execute_command brew install node@18
        echo "Changing permissions on /usr/local/include/node..."
        sudo chown -R $(whoami) /usr/local/include/node
        sudo chmod -R u+w /usr/local/include/node
        execute_command brew link --force --overwrite node@18
        if [ $? -ne 0 ]; then
            echo "Attempting to change permissions on /usr/local/share/doc/node..."
            sudo chown -R $(whoami) /usr/local/share/doc/node
            sudo chmod -R u+w /usr/local/share/doc/node
            execute_command brew link --force --overwrite node@18
        fi
    fi
fi

# Install Python if not present
if ! command_exists python3; then
    echo "Python is not installed, installing Python..."
    if [ "$OS" == "linux" ]; then
        execute_command sudo apt-get update
        execute_command sudo apt-get install -y python3 python3-pip
    elif [ "$OS" == "mac" ]; then
        execute_command brew install python
    fi
else
    echo "Python is already installed."
fi

# Install requirements from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    execute_command python3 -m pip install --upgrade pip
    execute_command python3 -m pip install -r requirements.txt --use-deprecated=legacy-resolver
else
    echo "requirements.txt not found, skipping Python packages installation."
fi

# Install Node.js packages
if [ -f "package.json" ]; then
    echo "Installing Node.js packages from package.json..."
    execute_command npm install
else
    echo "package.json not found, skipping Node.js packages installation."
fi

echo "Setup completed with the following errors (if any):"
cat errors.log
