# ----------------------------------------------------------------------------
#  File:        ROUND_ROBIN_README.md
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Documentation for the Round-Robin orchestration system implementation
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

# Celaya Multi-Agent Round-Robin Orchestration

This document explains the three-layer turn-scheduling system implemented in `orchestrator.py` that allows multiple Celaya agents to communicate efficiently without chaos.

## Core Architecture

The orchestration system consists of three layers:

| Layer                         | Purpose                                 | Implementation                                                                 |
| ----------------------------- | --------------------------------------- | ----------------------------------------------------------------------------- |
| **1. Baseline Scheduler**     | Fair, predictable rotation              | Classic round-robin with a "turn-token" via circular queue                     |
| **2. Interrupt Protocol**     | Let high-urgency messages jump the line | Priority heap with time-based and reputation-weighted interrupts               |
| **3. Arbitration & Recovery** | Handle deadlocks, conflicts, or silence | Timeouts, leader election, consensus ballots, and reputation tracking          |

## 1. Baseline Round-Robin Scheduler

The foundation of the system is a classic round-robin scheduler using a "turn token" approach:

- Agents are stored in a circular queue (`deque`)
- Each turn, one agent holds the token and speaks
- After speaking, the token passes to the next agent in the queue
- Every agent gets a fair chance to participate

Implementation details:
```python
# Round-Robin Scheduler (Layer 1)
self.turn_queue = deque(agents)
self.token_holder = None

# In orchestrate():
self.token_holder = self.turn_queue.popleft()
self.turn_queue.append(self.token_holder)  # Add back to end of queue
```

## 2. Interrupt Protocol

The second layer allows agents to request urgent interruptions based on priority:

- Interrupts are stored in a min-heap (priority queue)
- Each interrupt has a priority score (1-100), higher = more urgent
- Priority is adjusted by agent reputation
- Interrupts can preempt the current speaker if:
  - Current agent has spoken for at least MIN_SLICE seconds, or
  - Interrupt priority exceeds PREEMPT_THRESHOLD
- Paused agents are stored and resume after interrupts are handled

Key components:
```python
# Constants
MIN_SLICE = 1.5          # seconds
PREEMPT_THRESHOLD = 90   # interrupt score

# Interrupt Protocol (Layer 2)
self.interrupt_heap: List[Tuple[int, float, CelayaAgent, str]] = []
self.interrupt_depth = 0
self.paused_agents: deque = deque()

# Auto-detection in agent.speak()
if any(keyword in prompt.lower() for keyword in INTERRUPT_KEYWORDS):
    priority = 95  # High priority for urgent keywords
    await orchestrator.request_interrupt(self, priority, prompt)
```

## 3. Arbitration & Recovery

The third layer handles system failures, deadlocks, and conflict resolution:

### Timeout Protection
- Agents have a maximum time to respond (MAX_TURN_MS)
- Timeouts reduce agent reputation
- Repeated timeouts trigger leader election

### Leader Election
- When system issues occur, elect a leader based on reputation
- The leader agent coordinates recovery
- All agents are notified of the leadership change

### Consensus Ballots
- For disputed decisions, start consensus voting
- Requires quorum approval (default: 66%)
- All agents vote APPROVE/REJECT
- Results are broadcast once quorum reached

### Livelock Prevention
- Track interrupt depth to prevent interrupt loops
- If depth exceeds threshold, freeze interrupts for one cycle
- Ensures progress even with competing interrupts

## Agent Events

Agents can emit the following events:

| Event       | Description                                   | Usage                                      |
| ----------- | --------------------------------------------- | ------------------------------------------ |
| `INTERRUPT` | Request urgent attention                      | Critical information, security threats     |
| `HANDOFF`   | Transfer turn to specific agent               | Delegate to specialist agent               |
| `COMPLETE`  | Signal task completion before turn end        | Early task completion                      |
| `ERROR`     | Report an error condition                     | Exception handling, processing failures    |

## Reputation System

The system includes a reputation mechanism:

- Each agent has a reputation score (0.0-1.0)
- Reputation impacts interrupt priority: `effective = priority × (0.5 + reputation/2)`
- Reputation decreases from:
  - Timeouts (-0.2)
  - Errors (-0.1)
  - Slow responses (-0.05)
- Reputation is used for leader election

## Configuration

Key constants available for tuning:

```python
MIN_SLICE = 1.5            # Minimum seconds before interruption
MAX_TURN_MS = 5000         # Maximum milliseconds per turn
PREEMPT_THRESHOLD = 90     # Priority threshold for immediate interruption
QUORUM = 0.66              # Percentage required for consensus (66%)
MAX_INTERRUPT_DEPTH = 3    # Maximum interrupt depth before freezing
INTERRUPT_KEYWORDS = ["urgent", "critical", "emergency", "important", "!!"]
```

## Usage Examples

### Triggering an Interrupt

Agents can trigger interrupts via keywords or explicit API:

```python
# Via keywords (automatic)
response = await agent.speak("URGENT: Security breach detected!")

# Via explicit API
await orchestrator.request_interrupt(agent, 95, "Critical system failure")
```

### Handoff to Specialist Agent

When a task requires specialized knowledge:

```python
await agent.request_handoff("data_analyst", "Please analyze this sensor data", orchestrator)
```

### Consensus Decision

For important decisions requiring group agreement:

```python
await orchestrator.start_consensus_ballot("Should we allocate more resources to task X?")
# Agents will receive ballot and vote
await orchestrator.register_vote(agent, "Should we allocate more resources to task X?", "APPROVE")
```

## Benefits of this Approach

- **Fairness**: baseline round-robin ensures all agents get turns
- **Urgency**: interrupt protocol with priority enables time-sensitive responses
- **Resilience**: failure recovery mechanisms handle errors gracefully
- **Flexibility**: reputation and consensus enable adaptive behavior
- **Scalability**: designed to work with many agents without chaos

This architecture ensures efficient, organized communication while allowing for urgency and exception handling. 