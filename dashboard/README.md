# Celaya Multi-Agent Dashboard

A real-time dashboard for managing and monitoring multiple Celaya AI agents.

## Overview

The Celaya Multi-Agent Dashboard provides a terminal-based UI for:

- Sending commands to multiple AI agents in parallel
- Monitoring each agent's activities in its own terminal window
- Checking the health status of all connected agents
- Viewing log entries for actions and responses from each agent

## Features

- **Multi-agent display**: Each agent gets its own terminal window for activity monitoring
- **Real-time updates**: See agent responses as they happen
- **Parallel processing**: All agents work simultaneously on the same task
- **Command interface**: Simple command interface to interact with all agents at once
- **Health monitoring**: Check the health/availability of agent API endpoints
- **Log monitoring**: View and track agent activity through log files
- **Simulation mode**: Can operate in simulation mode without actual agent servers

## Usage

### Installation

1. Clone the repository
2. Make sure Go is installed on your system
3. Change to the dashboard directory
4. Install the required dependencies:

```
go mod tidy
```

### Running the Dashboard

From the dashboard directory:

```
go run .
```

Optional arguments:

- `--config path/to/config.json`: Specify a custom configuration file (default: `config.json`)
- `--logpath path/to/logs`: Specify a custom log directory (default: `logs`)
- `--timeout seconds`: Set API request timeout in seconds (default: 60)
- `--json`: Format logs as JSON (default: true)

### Simulation Mode

The dashboard operates in simulation mode by default, which means:

- It doesn't require actual Celaya agent servers to be running
- Responses are simulated based on agent roles
- Agent health is randomly simulated (with about 90% healthy)
- You can see the full dashboard functionality without setting up agent servers

To use real agent servers instead, modify the `simulateMode` flag in `api.go` to `false`.

### Commands

Type commands in the main terminal at the bottom of the screen:

- `health`: Check the health of all agents
- Any other text: Send as a command to all agents
- `quit` or `exit`: Exit the application
- Press `Ctrl+C` to exit at any time

## Configuration

The dashboard uses a configuration file (`config.json`) that defines:

- Agent details (name, URL, model, system prompt, role)
- Settings (default model, log path, etc.)

A default configuration is created on first run.

## Architecture

The dashboard consists of several key components:

- **Main Application**: Manages the UI and coordinates other components
- **API Client**: Communicates with the Celaya agent APIs (or simulates responses)
- **Logger**: Manages logging of agent activities
- **Orchestrator**: Coordinates parallel processing of commands
- **UI Components**: Terminal panels for each agent and the main interface

## Development

### Adding New Agents

To add new agents, modify the `config.json` file or update the `CreateDefaultConfig` function in `config.go`.

### Extending Functionality

Key files for extending functionality:

- `main.go`: Main application entry point
- `api.go`: API client for agent communication
- `orchestrator.go`: Agent coordination and parallel processing
- `log.go`: Logging utilities
- `config.go`: Configuration management

## License

BSL (Business Source License)

## Author

Christopher Celaya
chris@celayasolutions.com 