// ----------------------------------------------------------------------------
//  File:        agents.go
//  Project:     Celaya Solutions (Celaya Beats)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Implements agent types and behaviors for the Celaya Beats system
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package beats

import (
	"context"
	"fmt"
	"time"
)

// Common agent IDs
const (
	AgentLyra    AgentID = "Lyra"    // System health and monitoring
	AgentOtto    AgentID = "Otto"    // Routing and coordination
	AgentBeacon  AgentID = "Beacon"  // Message routing
	AgentLuma    AgentID = "Luma"    // Direct actions
	AgentArc     AgentID = "Arc"     // Vehicle control
	AgentVolt    AgentID = "Volt"    // Energy management
	AgentClarity AgentID = "Clarity" // Logging
	AgentEcho    AgentID = "Echo"    // Audit
)

// Common slot assignments
const (
	SlotHousekeeping Slot = 0 // System maintenance (Lyra)
	SlotRouting      Slot = 1 // Message routing (Otto/Beacon)
	SlotActions      Slot = 2 // Direct actions (Luma, Arc, Volt)
	SlotLogging      Slot = 3 // Logging and audit (Clarity, Echo)
	SlotPing         Slot = 4 // Out-of-turn messages
)

// ActionType defines the type of action an agent can perform
type ActionType string

// Common action types
const (
	ActionHealthCheck  ActionType = "HealthCheck"
	ActionRouteMessage ActionType = "RouteMessage"
	ActionStartVehicle ActionType = "StartVehicle"
	ActionLogEvent     ActionType = "LogEvent"
	ActionAuditEvent   ActionType = "AuditEvent"
)

// ActionPayload is a generic payload for agent actions
type ActionPayload struct {
	Type    ActionType  `json:"type"`
	Data    interface{} `json:"data,omitempty"`
	Created time.Time   `json:"created"`
}

// NewActionPayload creates a new action payload
func NewActionPayload(actionType ActionType, data interface{}) ActionPayload {
	return ActionPayload{
		Type:    actionType,
		Data:    data,
		Created: time.Now(),
	}
}

// Agent interface defines the basic behavior of an agent
type Agent interface {
	ID() AgentID
	Execute(ctx context.Context, event Event) error
}

// BaseAgent provides common functionality for all agents
type BaseAgent struct {
	id        AgentID
	scheduler *Scheduler
}

// NewBaseAgent creates a new base agent
func NewBaseAgent(id AgentID, scheduler *Scheduler) *BaseAgent {
	return &BaseAgent{
		id:        id,
		scheduler: scheduler,
	}
}

// ID returns the agent's identifier
func (a *BaseAgent) ID() AgentID {
	return a.id
}

// LyraAgent is responsible for system health and monitoring
type LyraAgent struct {
	*BaseAgent
}

// NewLyraAgent creates a new Lyra agent for system health monitoring
func NewLyraAgent(scheduler *Scheduler) *LyraAgent {
	agent := &LyraAgent{
		BaseAgent: NewBaseAgent(AgentLyra, scheduler),
	}

	// Register the agent with the scheduler
	scheduler.RegisterAgent(agent.ID(), agent.Execute)
	return agent
}

// Execute processes an event for the Lyra agent
func (a *LyraAgent) Execute(ctx context.Context, event Event) error {
	payload, ok := event.Payload.(ActionPayload)
	if !ok {
		return fmt.Errorf("invalid payload type for Lyra agent")
	}

	switch payload.Type {
	case ActionHealthCheck:
		return a.performHealthCheck(ctx, payload)
	default:
		return fmt.Errorf("unknown action type for Lyra agent: %s", payload.Type)
	}
}

// performHealthCheck runs a system health check
func (a *LyraAgent) performHealthCheck(ctx context.Context, payload ActionPayload) error {
	fmt.Printf("[Lyra] Performing health check at beat %d\n", a.scheduler.CurrentBeat())

	// Schedule a log event for this health check
	logPayload := NewActionPayload(ActionLogEvent, map[string]interface{}{
		"source":  "Lyra",
		"message": "Health check completed",
		"status":  "OK",
	})

	// Schedule the log event for the current beat in the logging slot
	a.scheduler.ScheduleEvent(
		a.scheduler.CurrentBeat(),
		SlotLogging,
		AgentClarity,
		logPayload,
	)

	return nil
}

// ArcAgent is responsible for vehicle control
type ArcAgent struct {
	*BaseAgent
}

// NewArcAgent creates a new Arc agent for vehicle control
func NewArcAgent(scheduler *Scheduler) *ArcAgent {
	agent := &ArcAgent{
		BaseAgent: NewBaseAgent(AgentArc, scheduler),
	}

	// Register the agent with the scheduler
	scheduler.RegisterAgent(agent.ID(), agent.Execute)
	return agent
}

// Execute processes an event for the Arc agent
func (a *ArcAgent) Execute(ctx context.Context, event Event) error {
	payload, ok := event.Payload.(ActionPayload)
	if !ok {
		return fmt.Errorf("invalid payload type for Arc agent")
	}

	switch payload.Type {
	case ActionStartVehicle:
		return a.startVehicle(ctx, payload)
	default:
		return fmt.Errorf("unknown action type for Arc agent: %s", payload.Type)
	}
}

// startVehicle starts a vehicle with the specified settings
func (a *ArcAgent) startVehicle(ctx context.Context, payload ActionPayload) error {
	data, ok := payload.Data.(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid data format for start vehicle action")
	}

	mode, _ := data["mode"].(string)
	temp, _ := data["temp"].(string)

	fmt.Printf("[Arc] Starting vehicle: mode=%s, temp=%s at beat %d\n",
		mode, temp, a.scheduler.CurrentBeat())

	// Schedule a log event for this vehicle start
	logPayload := NewActionPayload(ActionLogEvent, map[string]interface{}{
		"source":  "Arc",
		"message": fmt.Sprintf("Vehicle started with mode=%s, temp=%s", mode, temp),
		"status":  "OK",
	})

	// Schedule the log event for the current beat in the logging slot
	a.scheduler.ScheduleEvent(
		a.scheduler.CurrentBeat(),
		SlotLogging,
		AgentClarity,
		logPayload,
	)

	return nil
}

// ClarityAgent is responsible for logging events
type ClarityAgent struct {
	*BaseAgent
}

// NewClarityAgent creates a new Clarity agent for logging
func NewClarityAgent(scheduler *Scheduler) *ClarityAgent {
	agent := &ClarityAgent{
		BaseAgent: NewBaseAgent(AgentClarity, scheduler),
	}

	// Register the agent with the scheduler
	scheduler.RegisterAgent(agent.ID(), agent.Execute)
	return agent
}

// Execute processes an event for the Clarity agent
func (a *ClarityAgent) Execute(ctx context.Context, event Event) error {
	payload, ok := event.Payload.(ActionPayload)
	if !ok {
		return fmt.Errorf("invalid payload type for Clarity agent")
	}

	switch payload.Type {
	case ActionLogEvent:
		return a.logEvent(ctx, payload)
	default:
		return fmt.Errorf("unknown action type for Clarity agent: %s", payload.Type)
	}
}

// logEvent logs an event to the system
func (a *ClarityAgent) logEvent(ctx context.Context, payload ActionPayload) error {
	data, ok := payload.Data.(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid data format for log event action")
	}

	source, _ := data["source"].(string)
	message, _ := data["message"].(string)
	status, _ := data["status"].(string)

	fmt.Printf("[Clarity] Logging event: source=%s, message=%s, status=%s at beat %d\n",
		source, message, status, a.scheduler.CurrentBeat())

	// In a real implementation, we would persist this to a database or log file

	return nil
}
