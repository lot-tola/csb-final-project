#!/bin/bash


echo "Starting the backend server..."
cd /home/alvin/Documents/csb-final-project/Backend/ || exit
source venv/bin/activate
python3 app.py &
BACKEND_PID=$!

echo "Waiting for the backend server to initialize..."
sleep 10


echo "Starting the scheduler..."
cd ../scheduler || exit
python main.py &
SCHEDULER_PID=$!


echo "Backend PID: $BACKEND_PID"
echo "Scheduler PID: $SCHEDULER_PID"

wait $BACKEND_PID
wait $SCHEDULER_PID
