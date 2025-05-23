# Celaya Beats Scheduler

A time-slot based scheduling system for coordinating agent activities in the Celaya ecosystem.

## Overview

Celaya Beats is a fixed-duration time unit scheduler that allows multiple agents to coordinate their actions in a synchronized manner. The system ensures that all agents advance in lock-step, executing actions in predefined time slots within each beat.

Key features:
- Fixed-duration time units (beats/ticks)
- Predefined slots for different types of activities
- Multiple agent coordination
- Deterministic and auditable execution
- Timeline querying capabilities
- Real-time visualization of agent activities

## Core Concepts

- **Beat (CB)**: A fixed-duration time unit (configurable, default 500ms)
- **Slot**: Specific execution windows within each beat, assigned to different types of tasks:
  - Slot 0: System housekeeping (Lyra health checks)
  - Slot 1: Routing & coordination (Otto/Beacon)
  - Slot 2: Direct actions (Luma, Arc, Volt)
  - Slot 3: Logging & audit (Clarity, Echo)
  - Slot 4: Ping (reserved for out-of-turn messages)
- **Event**: A scheduled instruction for an agent to execute
- **Timeline**: An append-only log of all events that occur at each beat

## Agents

The system includes several built-in agents:
- **Lyra**: System health monitoring
- **Otto/Beacon**: Message routing and coordination
- **Arc**: Vehicle control
- **Luma**: Direct actions
- **Volt**: Energy management
- **Clarity**: Logging
- **Echo**: Audit

## Usage

### Building

To build the Celaya Beats CLI:

```bash
cd celaya-beats/cmd
go build -o celaya-beats-cli
```

To build the simulator with visualization:

```bash
cd celaya-beats/cmd/sim
go build -o celaya-beats-sim
```

### Running

Basic CLI usage:

```bash
./celaya-beats-cli
```

With custom beat duration:

```bash
./celaya-beats-cli -duration 1000
```

Run with demo events:

```bash
./celaya-beats-cli -demo
```

Run the user interaction simulator:

```bash
./celaya-beats-sim
```

Disable visualization in the simulator:

```bash
./celaya-beats-sim -no-visuals
```

### CLI Commands

Once running the CLI, you can interact with the system using the following commands:

- `status`: Show current beat and scheduler status
- `events [beat]`: Show events at the specified beat
- `schedule [beat] [agent] [action]`: Schedule a new event
- `lyra [beat]`: Schedule a Lyra health check
- `arc [beat] [mode] [temp]`: Schedule an Arc vehicle start
- `now`: Show current beat time
- `noon`: Show events at noon today
- `help`: Show all available commands
- `quit`: Exit the program

## Simulator and Visualization

The Celaya Beats system includes a simulator that demonstrates how agents coordinate and work in parallel. The simulator:

1. Creates all agent types (Lyra, Otto, Arc, Luma, Clarity, Echo)
2. Simulates user messages directed to specific agents
3. Visualizes what each agent is doing at every beat
4. Shows agent dependencies and coordination
5. Produces a timeline of all activities

The visualization output looks like this:

```
================ BEAT 10 ================
Time: 2025-05-15T10:22:30Z

Otto     │ Routing message: @Arc Start cooling the car to 68°F [RouteMessage] (Slot 1)
Lyra     │ IDLE
Arc      │ IDLE
Luma     │ IDLE
Clarity  │ Logging: Routed message to Arc: @Arc Start cooling the car to 68°F [LogEvent] (Slot 3)
Echo     │ IDLE

================ BEAT 11 ================
Time: 2025-05-15T10:22:30.5Z

Otto     │ IDLE
Lyra     │ IDLE
Arc      │ Starting vehicle: mode=cool, temp=68°F [StartVehicle] (Slot 2)
Luma     │ IDLE
Clarity  │ IDLE
Echo     │ Auditing event: User message to Arc: @Arc Start cooling the car to 68°F [AuditEvent] (Slot 3)
```

## Examples

Using the CLI:

```
> status
Current beat: 45 (Time: 2025-05-15T10:22:30Z)

> lyra 50
Scheduled Lyra health check at beat 50

> arc 55 cool 68F
Scheduled Arc vehicle action at beat 55: mode=cool, temp=68F

> events 50
Events at beat 50 (Time: 2025-05-15T10:22:35Z):
  [Housekeeping] Agent: Lyra, Action: HealthCheck

> events 55
Events at beat 55 (Time: 2025-05-15T10:22:37.5Z):
  [Actions] Agent: Arc, Action: StartVehicle
  [Logging] Agent: Clarity, Action: LogEvent
```

## Integration

The Celaya Beats scheduler can be integrated with other components by importing the package and creating a scheduler instance:

```go
import "github.com/celaya/celaya/celaya-beats"

// Create a scheduler with 500ms beats
scheduler := beats.NewScheduler(500 * time.Millisecond)

// Register slots and agents
scheduler.RegisterSlot(beats.SlotHousekeeping, "Housekeeping")
lyra := beats.NewLyraAgent(scheduler)

// Start the scheduler
scheduler.Start()
defer scheduler.Stop()

// Schedule events
healthCheckPayload := beats.NewActionPayload(beats.ActionHealthCheck, nil)
scheduler.ScheduleEvent(10, beats.SlotHousekeeping, beats.AgentLyra, healthCheckPayload)
``` 