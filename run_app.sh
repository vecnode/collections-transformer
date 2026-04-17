#!/bin/bash

# Script to launch both client and server in separate terminal windows
# Tracks processes for cleanup on exit

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_DIR="${SCRIPT_DIR}/client"
SERVER_DIR="${SCRIPT_DIR}/server"
SCRIPTS_DIR="${SCRIPT_DIR}/scripts"

# Arrays to store terminal window PIDs
TERMINAL_PIDS=()

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "Cleaning up processes"
    
    # Kill all terminal windows we launched
    for pid in "${TERMINAL_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Killing terminal process $pid"
            kill -TERM "$pid" 2>/dev/null
            sleep 0.5
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null
            fi
        fi
    done
    
    # Kill npm/node processes in client directory
    pkill -f "npm run dev" 2>/dev/null
    pkill -f "next dev" 2>/dev/null
    
    # Kill python processes running app.py in server directory
    pkill -f "python3.*app.py" 2>/dev/null
    pkill -f "python.*app.py" 2>/dev/null
    
    # Kill any remaining child processes of this script
    pkill -P $$ 2>/dev/null
    
    echo "Cleanup complete."
    exit 0
}

# Set up signal handlers (only cleanup on explicit Ctrl+C in main script)
trap cleanup SIGINT SIGTERM

# Detect available terminal emulator
if command -v gnome-terminal &> /dev/null; then
    TERMINAL_CMD="gnome-terminal"
    TERMINAL_OPTS="--"
elif command -v xterm &> /dev/null; then
    TERMINAL_CMD="xterm"
    TERMINAL_OPTS="-e"
elif command -v konsole &> /dev/null; then
    TERMINAL_CMD="konsole"
    TERMINAL_OPTS="-e"
elif command -v x-terminal-emulator &> /dev/null; then
    TERMINAL_CMD="x-terminal-emulator"
    TERMINAL_OPTS="-e"
else
    echo "Error: No suitable terminal emulator found. Please install gnome-terminal, xterm, or konsole."
    exit 1
fi

# Launch server first
echo "Launching server (python3 app.py) in terminal window..."
"$TERMINAL_CMD" --title="Server - Collections Transformer" --working-directory="$SERVER_DIR" $TERMINAL_OPTS bash -c "\
\"${SCRIPTS_DIR}/run_server.sh\"; \
exec bash" &
TERMINAL_PIDS+=($!)

# Wait 4 seconds for server to start and AI models to initialize
echo "Waiting 4 seconds for server to start and AI models to initialize..."
sleep 4

# Launch client in second terminal window
echo "Launching client (npm run dev) in terminal window..."
"$TERMINAL_CMD" --title="Client - Collections Transformer" --working-directory="$CLIENT_DIR" $TERMINAL_OPTS bash -c "\
\"${SCRIPTS_DIR}/run_client.sh\"; \
exec bash" &
TERMINAL_PIDS+=($!)

echo ""
echo "Both terminals launched!"
echo "Terminal PIDs: ${TERMINAL_PIDS[@]}"
echo ""
echo "Press Ctrl+C to stop all processes and close terminals."
echo ""

# Wait for user interrupt
wait

