#!/bin/bash

# Navigate to the backend directory and start the server
echo "Starting the backend server..."
cd ../Backend || exit
source venv/bin/activate
python3 app.py &
BACKEND_PID=$!

# Wait for the backend to initialize (adjust if necessary)
echo "Waiting for the backend server to initialize..."
sleep 10

# Navigate to the scheduler directory and run the scheduler
echo "Starting the scheduler..."
cd ../scheduler || exit
python main.py &
SCHEDULER_PID=$!

# Keep track of process IDs
echo "Backend PID: $BACKEND_PID"
echo "Scheduler PID: $SCHEDULER_PID"

# Wait for processes to finish (optional)
wait $BACKEND_PID
wait $SCHEDULER_PID
