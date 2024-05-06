#!/bin/bash

# Start the bot process in the background
python bot.py &

# Start the uvicorn server for FastAPI in the foreground
uvicorn main:app --host 0.0.0.0 --port 8000