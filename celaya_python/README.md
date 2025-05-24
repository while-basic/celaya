# Celaya Consensus Framework

A multi-agent consensus framework for the Celaya runtime.

## Overview

The Celaya Consensus Framework provides a system for multi-agent consensus, allowing agents to propose, vote on, and reach consensus on various actions and decisions. It includes:

- Agent registration system
- Asynchronous message bus
- Ticker for synchronization
- Consensus manager for voting and decision-making
- CLI integration with Celaya

## Installation

### Prerequisites

- Python 3.10 or higher
- Celaya runtime

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

## Usage

### Register an Agent

```python
from celaya_python.agents import register_agent

@register_agent(name="my_agent")
class MyAgent:
    """Custom agent implementation."""
    
    def __init__(self):
        self.name = "my_agent"
    
    async def process_message(self, message):
        # Process incoming messages
        pass
```

### Use the Message Bus

```python
import asyncio
from celaya_python.runtime.bus import Bus

async def main():
    # Create a bus
    bus = Bus()
    
    # Create private queues
    bus.create_private_queue("agent1")
    bus.create_private_queue("agent2")
    
    # Subscribe to topics
    bus.subscribe("agent1", "events")
    bus.subscribe("agent2", "events")
    
    # Publish a message
    bus.publish("events", {"type": "notification", "content": "Hello!"}, sender_id="system")
    
    # Get messages
    queue1 = bus.get_queue("agent1")
    message = await queue1.get()
    print(f"Agent1 received: {message.payload}")

asyncio.run(main())
```

### Create a Consensus Proposal

```python
import asyncio
from celaya_python.runtime.bus import Bus
from celaya_python.runtime.consensus import ConsensusManager, VoteType

async def main():
    # Create a bus and consensus manager
    bus = Bus()
    consensus = ConsensusManager(bus)
    
    # Start the consensus manager
    await consensus.start()
    
    # Create a proposal
    proposal_id = consensus.create_proposal(
        proposal_type="ACTION",
        content={"action": "do_something", "parameters": {}},
        proposer_id="agent1"
    )
    
    # Vote on the proposal
    consensus.cast_vote(proposal_id, "agent2", VoteType.APPROVE)
    consensus.cast_vote(proposal_id, "agent3", VoteType.APPROVE)
    
    # Wait for consensus to be reached
    await asyncio.sleep(1)
    
    # Check the proposal status
    proposal = consensus.proposals.get(proposal_id)
    if proposal:
        print(f"Proposal status: {proposal.status}")

asyncio.run(main())
```

### Use the CLI

```bash
# Boot the Lyra OS kernel
celaya_python boot --config path/to/config.yaml

# Run a model as an agent
celaya_python run llama3:8b --agent-id my_agent
```

## Architecture

The framework consists of several key components:

1. **Agent Registration**: A decorator-based system for registering agent classes.
2. **Message Bus**: An async pub-sub wrapper around asyncio.Queue for inter-agent communication.
3. **Ticker**: Emits regular tick events for synchronization.
4. **Consensus Manager**: Handles proposals, voting, and consensus decisions.
5. **CLI**: Command-line interface for interacting with the framework.

## Development

### Running Tests

```bash
pytest tests/
```

### Building Documentation

```bash
cd docs
make html
```

## License

This project is licensed under the Business Source License (BUSL) - see the LICENSE file for details. 