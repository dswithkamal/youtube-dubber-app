#!/bin/bash

# Update package list
sudo apt-get update

# Install system dependencies
sudo apt-get install -y ffmpeg python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
