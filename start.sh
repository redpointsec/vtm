#!/bin/bash

# Start Streamlit server
echo "Starting Streamlit server..."
cd chatbot
streamlit run main.py &
cd ..
# Save the PID of the Streamlit process
STREAMLIT_PID=$!

# Start Django server
echo "Starting Django server..."
./manage.py runserver

# Wait for the Django server to exit
wait $!

# If the Django server stops, kill the Streamlit process
echo "Stopping Streamlit server..."
kill $STREAMLIT_PID

