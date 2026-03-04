#!/bin/bash
set -e

# Start the main process in its own process group
# The '-' before "$@" tells bash to start in a new process group
# so signals can be sent to all subprocesses
setsid "$@" &
child_pid=$!

# Function to forward signals to the entire process group
forward_signal() {
    sig=$1
    echo "Received signal $sig, forwarding to child process group..."
    # Use negative PID to signal the entire group
    kill -s "$sig" -"$child_pid" 2>/dev/null
}

# Trap termination signals
for sig in INT TERM HUP QUIT; do
    trap "forward_signal $sig" "$sig"
done

# Wait for the main process
wait $child_pid
exit_code=$?
echo "Child process exited with code $exit_code"
exit $exit_code
