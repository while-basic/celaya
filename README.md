# Multi-Agent Dashboard

The Multi-Agent Dashboard is a terminal-based UI for monitoring and interacting with multiple agents in parallel. It provides a centralized interface for sending commands to agents, viewing their responses, and managing agent interactions.

## Features

### Core Features
- **Parallel Agent Monitoring**: View all agent activities in separate terminal panels
- **Central Command Interface**: Send commands to all agents from a single input
- **Health Monitoring**: Check agent availability and status
- **Color-Coded Interface**: Visual indicators for different message types and agent states
- **JSON Logging**: Detailed logs stored for each agent

### Advanced Features
- **Direct Messaging**: Send messages to specific agents using `dm <agent> <message>`
- **Focus Mode**: Select specific agents to focus on with `focus <agent1> <agent2> ...`
- **Agent Groups**: Group agents for targeted commands using `group <groupname> <message>`
- **Command Templates**: Use templates for common tasks with `template <name> [args]`
- **Command History**: Navigate through previous commands with arrow keys

## Getting Started

### Prerequisites
- Go 1.18 or higher
- Terminal with color support

### Installation
1. Clone the repository
2. Navigate to the project directory
3. Run the dashboard:
   ```
   ./run_dashboard.sh
   ```

### Configuration
The dashboard is configured using a `config.json` file. A default configuration is created on the first run, which you can customize. The configuration defines:

- Agent profiles (name, model, role, URL)
- Agent groups
- Command templates
- Dashboard settings

## Using the Dashboard

### Command Reference

| Command | Description |
|---------|-------------|
| `health` | Check the health status of all agents |
| `focus <agent1> <agent2> ...` | Focus on specific agents (commands only go to focused agents) |
| `unfocus <agent1> <agent2> ...` | Remove focus from agents |
| `unfocus all` | Remove focus from all agents |
| `dm <agent> <message>` | Send a direct message to a specific agent |
| `group <groupname> <message>` | Send a message to a predefined group of agents |
| `groups` | List available agent groups |
| `template <name> [args]` | Use a command template |
| `templates` | List available templates |
| `help` | Show available commands |
| `quit` or `exit` | Exit the application |

Any other input is treated as a command to be sent to all agents (or focused agents if focus is active).

### Simulation Mode

The dashboard supports a simulation mode for testing without actual agent servers. In this mode, the dashboard generates realistic responses based on agent roles and command content.

To run in simulation mode:
```
DASHBOARD_SIM_MODE=true ./agent_dashboard
```

Or use the provided script:
```
./run_dashboard.sh
```

## License

This project is licensed under the Business Source License (BSL) - see the LICENSE file for details.

## Contact

Christopher Celaya - [chris@celayasolutions.com](mailto:chris@celayasolutions.com)
