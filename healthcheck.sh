#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install required package if not already installed
pip install colorama >/dev/null 2>&1

# Make the Python script executable
chmod +x health_check.py

# Run the health check
python3 health_check.py

# Store the exit code
exit_code=$?

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit $exit_code
