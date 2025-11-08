#!/bin/bash
# Start the Franklin County Vote Analysis Web App

cd "$(dirname "$0")/.."
source .venv/bin/activate
cd webapp
python app.py

