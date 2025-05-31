#!/bin/bash

set -e
set -o pipefail

LOG_FILE="setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Timestamp each command
PS4='+ [$(date "+%Y-%m-%d %H:%M:%S")] '
export PS4
set -x

# Message functions
info() { echo -e "\033[1;34m[INFO]\033[0m $1"; }
error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; exit 1; }

info "Starting setup script. Logs will be written to $LOG_FILE"

# Ensure script is run with sudo/root privileges
if [[ "$EUID" -ne 0 ]]; then
  error "Please run this script with sudo or as root."
fi

info "Updating package lists..."
apt-get update || error "Failed to update packages."

info "Upgrading packages..."
apt-get upgrade -y || error "Failed to upgrade packages."

info "Installing python3.12-venv..."
apt-get install -y python3.12-venv || error "Failed to install python3.12-venv."

# Check if python3.12 exists
if ! command -v python3.12 &>/dev/null; then
  error "Python 3.12 not found. Please ensure it's installed correctly."
fi

info "Creating virtual environment..."
sudo -u "$SUDO_USER" python3.12 -m venv .venv || error "Failed to create virtual environment."

info "Activating virtual environment..."
source .venv/bin/activate || error "Failed to activate virtual environment."

info "Cloning repository..."
if [[ -d "slack-ragbot" ]]; then
  info "Repository 'slack-ragbot' already exists. Skipping clone."
else
  git clone https://github.com/robdnh/slack-ragbot.git || error "Failed to clone repository."
fi

cd slack-ragbot/slackbot || error "Directory 'slack-ragbot/slackbot' not found."

info "Installing Python dependencies..."
pip install --upgrade pip || error "Failed to upgrade pip."
pip install -r requirements.txt || error "Failed to install Python dependencies."

info "Setup completed successfully."
