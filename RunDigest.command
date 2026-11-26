#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
echo "Done! You can close this window."
