#!/bin/bash
# ----------------------------------------------------------------------------
#  File:        run_dashboard.sh
#  Project:     Celaya Solutions (Agent Dashboard)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Script to run the agent dashboard with simulation mode
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

# Get the absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DASHBOARD_DIR="$SCRIPT_DIR/dashboard"

# Ensure dashboard directory exists
if [ ! -d "$DASHBOARD_DIR" ]; then
  echo "Dashboard directory not found at $DASHBOARD_DIR!"
  exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$DASHBOARD_DIR/logs"

# Build the dashboard
echo "Building dashboard..."
cd "$DASHBOARD_DIR" && go build -o agent_dashboard . || { echo "Build failed!"; exit 1; }

# Run the dashboard with simulation mode
echo "Starting dashboard in simulation mode..."
cd "$DASHBOARD_DIR" && DASHBOARD_SIM_MODE=true ./agent_dashboard --logpath=logs

echo "Dashboard exited." 