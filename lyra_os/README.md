# Lyra OS

A micro-kernel operating system for multi-agent consensus in Celaya.

## Overview

Lyra OS is a specialized operating system built for managing multi-agent consensus systems. It provides a kernel, boot sequence, agent management, and consensus mechanisms to ensure reliable and secure agent interactions.

## Features

- **Micro-kernel Architecture**: Lightweight core with modular services
- **Agent Management**: Dynamic loading and lifecycle management of agents
- **Consensus System**: Built-in consensus mechanisms for agent decision-making
- **Secure Communications**: ED25519 key management and authentication
- **Trust Management**: Weighted voting and trust tracking
- **Content Addressing**: IPFS-style content identification for consensus records
- **Cinematic Boot Sequence**: Visually appealing boot animation

## Installation

### Prerequisites

- Python 3.10 or higher
- Celaya runtime
- Rich library (for animations)
- PyYAML (for configuration)
- Cryptography library (for key management)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/celaya/celaya.git
   cd celaya
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

3. Make the `lyra` command executable:
   ```bash
   chmod +x lyra_os/bin/lyra
   ```

## Usage

### Starting Lyra OS

```bash
# Start the Lyra OS kernel
lyra start

# Start with a custom configuration
lyra start --config /path/to/bootstrap.yaml

# Start with debug logging
lyra start --debug

# Start in the background
lyra start --background
```

### Checking Status

```bash
# Check if Lyra OS is running
lyra status

# Get detailed status information
lyra status --verbose
```

### Stopping Lyra OS

```bash
# Stop Lyra OS gracefully
lyra stop

# Force stop Lyra OS
lyra stop --force
```

## Configuration

Lyra OS uses YAML configuration files:

### bootstrap.yaml

Defines the agents to load during boot:

```yaml
system:
  name: "Lyra OS"
  version: "1.0.0"
  tick_interval_ms: 1000

agents:
  - id: "strategist"
    model: "llama3:70b"
    catchphrase: "Analyzing strategic options for optimal outcomes."
    role: "Strategist"
    required: true
    weight: 1.0
  
  # Additional agents...
```

### quorum.yaml

Defines the consensus rules:

```yaml
global:
  default_threshold: 0.66
  minimum_participants: 3

k_of_n_rules:
  BOOT_CONSENSUS:
    k: 3
    n: 5
    threshold: 0.66

veto_powers:
  strategist:
    - BOOT_CONSENSUS
    - EXTERNAL_COMMUNICATION
```

## Architecture

Lyra OS consists of several key components:

1. **Kernel**: Core service that manages the system lifecycle
2. **Boot Sequence**: Process for initializing agents and establishing consensus
3. **Message Bus**: Communication system for inter-agent messaging
4. **Consensus Manager**: System for proposal creation and voting
5. **Keyring**: ED25519 key management for agent authentication
6. **Ledger**: Trust weight tracking and CID cache
7. **Animation**: Terminal graphics for the boot sequence

## Development

### Directory Structure

```
lyra_os/
├─ kernel/           # Core kernel services
├─ agents/           # Agent symbolic links
├─ conf/             # Configuration files
└─ bin/              # Command-line tools
```

### Extending Lyra OS

To create a custom agent:

1. Implement your agent class
2. Register it with `@register_agent`
3. Add it to the bootstrap configuration

## License

This project is licensed under the Business Source License (BUSL) - see the LICENSE file for details. 