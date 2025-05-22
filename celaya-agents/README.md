# Celaya Agent Orchestration System

A multi-agent communication system using Celaya to orchestrate interactions between 11 specialized agents.

## Overview

This system implements an 11-agent orchestration framework where each agent has a specialized role and personality. The agents communicate through a central orchestrator, allowing for structured turn-taking and private messaging.

## System Components

- **Celaya Instances**: 11 separate instances of Celaya (Ollama fork) running on different ports
- **Python Orchestrator**: Manages the flow of communication between agents
- **Agent Configuration**: JSON-based configuration for agent personalities and system prompts

## Agent Roles

| Agent    | Role                  | Description                                           |
|----------|------------------------|-------------------------------------------------------|
| Echo     | Communicator           | Streamlines and clarifies communication               |
| Verdict  | Decision Maker         | Makes clear, decisive judgments                       |
| Vitals   | Health Monitor         | Assesses system wellbeing and functionality           |
| Core     | Foundation Builder     | Establishes robust principles and frameworks          |
| Theory   | Conceptual Thinker     | Develops novel ideas and theoretical frameworks       |
| Sentinel | Guardian               | Protects integrity and identifies vulnerabilities     |
| Beacon   | Guide                  | Illuminates paths forward, providing direction        |
| Lens     | Perspective Shifter    | Reframes discussions from different angles            |
| Volt     | Energizer              | Invigorates discussions with enthusiasm               |
| Clarity  | Simplifier             | Distills complex ideas into clear concepts            |
| Arkive   | Historian              | Maintains records and provides context                |

## Installation

### Prerequisites

- Python 3.8+
- Celaya binary
- Required Python packages: `requests`, `psutil`

Install required packages:

```bash
pip install requests psutil
```

### Setup

1. Clone or download this repository
2. Install required Python packages:

```bash
pip install -r requirements.txt
```

3. Make sure your Celaya binary is executable:

```bash
chmod +x ../celaya
```

## Usage

### Setting up agent instances

To start all agents:

```bash
python setup_agents.py --celaya ../celaya --pull-models
```

This command:
- Starts 11 Celaya instances (one for each agent)
- Assigns each instance to a unique port
- Configures each agent with its specified system prompt

### Running the orchestrator

To begin the conversation:

```bash
python orchestrator.py --config agent_config.json --prompt "Discuss the future of AI and ethics"
```

You can customize the initial prompt to start a conversation on any topic.

### Controlling the conversation

- Set maximum turns with `--max-turns`
- Use custom configuration file with `--config`
- Conversation logs are saved automatically to `conversation_log.json`

## Advanced Features

### Agent-to-Agent Direct Messaging

Agents can send private messages to each other:

```python
await direct_message(sender_agent, "RecipientName", "Private message content", orchestrator)
```

### Custom Agent Configuration

Edit `agent_config.json` to:
- Change system prompts
- Modify agent roles
- Adjust API settings

## Troubleshooting

- If ports are already in use, the setup script will exit with an error
- Check log files in the `logs` directory for detailed error messages
- Ensure Celaya binary has correct permissions

## Extending the System

### Additional Agents

To add a new agent:
1. Add the agent configuration to `agent_config.json`
2. Update port assignments to avoid conflicts
3. Add any specialized system prompts

### Priority-Based Orchestration

The current system uses round-robin orchestration. For priority-based orchestration:
1. Modify the `Orchestrator.orchestrate()` method
2. Implement logic to prioritize specific agents based on context

## License

BSL (Business Source License)

## Author

Christopher Celaya
chris@celayasolutions.com 