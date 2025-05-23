// ----------------------------------------------------------------------------
//  File:        agents_simulator.go
//  Project:     Celaya Solutions (Celaya Beats)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Additional agent implementations and user interaction simulator
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package beats

import (
	"context"
	"fmt"
	"strings"
	"time"
)

// UserMessage represents a message from a user to the system
type UserMessage struct {
	Text      string
	Timestamp time.Time
	Target    AgentID // Target agent, if specified
}

// OttoAgent is responsible for routing messages
type OttoAgent struct {
	*BaseAgent
}

// NewOttoAgent creates a new Otto agent for message routing
func NewOttoAgent(scheduler *Scheduler) *OttoAgent {
	agent := &OttoAgent{
		BaseAgent: NewBaseAgent(AgentOtto, scheduler),
	}

	// Register the agent with the scheduler
	scheduler.RegisterAgent(agent.ID(), agent.Execute)
	return agent
}

// Execute processes an event for the Otto agent
func (a *OttoAgent) Execute(ctx context.Context, event Event) error {
	payload, ok := event.Payload.(ActionPayload)
	if !ok {
		return fmt.Errorf("invalid payload type for Otto agent")
	}

	switch payload.Type {
	case ActionRouteMessage:
		return a.routeMessage(ctx, payload)
	default:
		return fmt.Errorf("unknown action type for Otto agent: %s", payload.Type)
	}
}

// routeMessage routes a message to the appropriate agent
func (a *OttoAgent) routeMessage(ctx context.Context, payload ActionPayload) error {
	data, ok := payload.Data.(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid data format for route message action")
	}

	message, _ := data["message"].(string)
	targetStr, _ := data["target"].(string)
	target := AgentID(targetStr)

	fmt.Printf("[Otto] Routing message: %s to %s at beat %d\n",
		message, target, a.scheduler.CurrentBeat())

	// Parse the message and schedule appropriate actions
	// This is a simplified implementation for the demo
	switch target {
	case AgentLyra:
		// Schedule a health check
		healthCheckPayload := NewActionPayload(ActionHealthCheck, nil)
		a.scheduler.ScheduleEvent(
			a.scheduler.CurrentBeat()+1,
			SlotHousekeeping,
			AgentLyra,
			healthCheckPayload,
		)

	case AgentArc:
		// Parse the message to extract parameters
		// In a real implementation, we would use NLP to extract intent
		mode := "auto"
		temp := "72°F"

		// If the message contains "cool" or "heat", use that mode
		if contains(message, "cool") {
			mode = "cool"
		} else if contains(message, "heat") {
			mode = "heat"
		}

		// Schedule a vehicle start action
		vehiclePayload := NewActionPayload(ActionStartVehicle, map[string]interface{}{
			"mode": mode,
			"temp": temp,
		})
		a.scheduler.ScheduleEvent(
			a.scheduler.CurrentBeat()+1,
			SlotActions,
			AgentArc,
			vehiclePayload,
		)

	case AgentLuma:
		// Schedule a direct action
		actionPayload := NewActionPayload(ActionStartVehicle, map[string]interface{}{
			"mode":    "custom",
			"message": message,
		})
		a.scheduler.ScheduleEvent(
			a.scheduler.CurrentBeat()+1,
			SlotActions,
			AgentLuma,
			actionPayload,
		)
	}

	// Schedule a log event for this message routing
	logPayload := NewActionPayload(ActionLogEvent, map[string]interface{}{
		"source":  "Otto",
		"message": fmt.Sprintf("Routed message to %s: %s", target, message),
		"status":  "OK",
	})

	a.scheduler.ScheduleEvent(
		a.scheduler.CurrentBeat(),
		SlotLogging,
		AgentClarity,
		logPayload,
	)

	return nil
}

// LumaAgent is responsible for direct actions
type LumaAgent struct {
	*BaseAgent
}

// NewLumaAgent creates a new Luma agent for direct actions
func NewLumaAgent(scheduler *Scheduler) *LumaAgent {
	agent := &LumaAgent{
		BaseAgent: NewBaseAgent(AgentLuma, scheduler),
	}

	// Register the agent with the scheduler
	scheduler.RegisterAgent(agent.ID(), agent.Execute)
	return agent
}

// Execute processes an event for the Luma agent
func (a *LumaAgent) Execute(ctx context.Context, event Event) error {
	payload, ok := event.Payload.(ActionPayload)
	if !ok {
		return fmt.Errorf("invalid payload type for Luma agent")
	}

	switch payload.Type {
	case ActionStartVehicle:
		return a.performCustomAction(ctx, payload)
	default:
		return fmt.Errorf("unknown action type for Luma agent: %s", payload.Type)
	}
}

// performCustomAction executes a custom action based on user input
func (a *LumaAgent) performCustomAction(ctx context.Context, payload ActionPayload) error {
	data, ok := payload.Data.(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid data format for custom action")
	}

	mode, _ := data["mode"].(string)
	message, _ := data["message"].(string)

	fmt.Printf("[Luma] Performing custom action: mode=%s, message=%s at beat %d\n",
		mode, message, a.scheduler.CurrentBeat())

	// Schedule a log event for this action
	logPayload := NewActionPayload(ActionLogEvent, map[string]interface{}{
		"source":  "Luma",
		"message": fmt.Sprintf("Performed custom action: %s", message),
		"status":  "OK",
	})

	a.scheduler.ScheduleEvent(
		a.scheduler.CurrentBeat(),
		SlotLogging,
		AgentClarity,
		logPayload,
	)

	return nil
}

// EchoAgent is responsible for audit
type EchoAgent struct {
	*BaseAgent
}

// NewEchoAgent creates a new Echo agent for auditing
func NewEchoAgent(scheduler *Scheduler) *EchoAgent {
	agent := &EchoAgent{
		BaseAgent: NewBaseAgent(AgentEcho, scheduler),
	}

	// Register the agent with the scheduler
	scheduler.RegisterAgent(agent.ID(), agent.Execute)
	return agent
}

// Execute processes an event for the Echo agent
func (a *EchoAgent) Execute(ctx context.Context, event Event) error {
	payload, ok := event.Payload.(ActionPayload)
	if !ok {
		return fmt.Errorf("invalid payload type for Echo agent")
	}

	switch payload.Type {
	case ActionAuditEvent:
		return a.auditEvent(ctx, payload)
	default:
		return fmt.Errorf("unknown action type for Echo agent: %s", payload.Type)
	}
}

// auditEvent performs an audit of an event
func (a *EchoAgent) auditEvent(ctx context.Context, payload ActionPayload) error {
	data, ok := payload.Data.(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid data format for audit event")
	}

	event, _ := data["event"].(string)

	fmt.Printf("[Echo] Auditing event: %s at beat %d\n",
		event, a.scheduler.CurrentBeat())

	return nil
}

// UserSimulator simulates user interaction with the system
type UserSimulator struct {
	scheduler   *Scheduler
	messages    []UserMessage
	visualState *VisualState
}

// NewUserSimulator creates a new user simulator
func NewUserSimulator(scheduler *Scheduler, visualState *VisualState) *UserSimulator {
	return &UserSimulator{
		scheduler:   scheduler,
		messages:    []UserMessage{},
		visualState: visualState,
	}
}

// AddMessage adds a user message to the simulation
func (s *UserSimulator) AddMessage(message UserMessage) {
	s.messages = append(s.messages, message)
}

// AddDefaultScenario adds a predefined scenario of user interactions
func (s *UserSimulator) AddDefaultScenario() {
	// Add a series of messages that simulate a conversation
	baseTime := time.Now()

	s.AddMessage(UserMessage{
		Text:      "@Lyra Can you check the system status?",
		Timestamp: baseTime.Add(2 * time.Second),
		Target:    AgentLyra,
	})

	s.AddMessage(UserMessage{
		Text:      "@Arc Start cooling the car to 68°F",
		Timestamp: baseTime.Add(5 * time.Second),
		Target:    AgentArc,
	})

	s.AddMessage(UserMessage{
		Text:      "@Luma Set a reminder for my meeting at 3pm",
		Timestamp: baseTime.Add(8 * time.Second),
		Target:    AgentLuma,
	})

	s.AddMessage(UserMessage{
		Text:      "@Arc Change to heating mode at 72°F",
		Timestamp: baseTime.Add(12 * time.Second),
		Target:    AgentArc,
	})
}

// RunSimulation runs the user interaction simulation
func (s *UserSimulator) RunSimulation(ctx context.Context, visualizationMode bool) {
	if len(s.messages) == 0 {
		fmt.Println("No messages to simulate")
		return
	}

	// Sort messages by timestamp
	// In a real implementation, we would sort the messages

	// Start time for the simulation
	startTime := time.Now()

	fmt.Println("Starting user interaction simulation...")
	fmt.Println("--------------------------------------")

	for _, message := range s.messages {
		// Calculate when to send this message based on its timestamp
		elapsedTime := message.Timestamp.Sub(s.messages[0].Timestamp)
		targetTime := startTime.Add(elapsedTime)

		// Wait until it's time to send this message
		waitDuration := time.Until(targetTime)
		if waitDuration > 0 {
			time.Sleep(waitDuration)
		}

		// Display the user message
		fmt.Printf("\nUSER: %s\n", message.Text)

		// Process the message
		s.processUserMessage(message)

		// In visualization mode, wait for the next update and show the state
		if visualizationMode {
			// Wait a bit for all events to process
			time.Sleep(1 * time.Second)

			// Show the current beat visualization
			currentBeat := s.scheduler.CurrentBeat()
			fmt.Println(s.visualState.FormatBeatVisualization(currentBeat - 1))
		}
	}

	// Show final state after all messages
	if visualizationMode {
		fmt.Println("\nFinal system state:")
		fmt.Println("-------------------")
		currentBeat := s.scheduler.CurrentBeat()
		fmt.Println(s.visualState.FormatTimelineVisualization(0, currentBeat-1))
	}
}

// processUserMessage handles a user message and routes it to the appropriate agent
func (s *UserSimulator) processUserMessage(message UserMessage) {
	// Route the message through Otto
	if message.Target != "" {
		routePayload := NewActionPayload(ActionRouteMessage, map[string]interface{}{
			"message": message.Text,
			"target":  string(message.Target),
		})

		// Schedule the routing event for the current beat
		currentBeat := s.scheduler.CurrentBeat()
		s.scheduler.ScheduleEvent(currentBeat, SlotRouting, AgentOtto, routePayload)

		// Also schedule an audit event
		auditPayload := NewActionPayload(ActionAuditEvent, map[string]interface{}{
			"event": fmt.Sprintf("User message to %s: %s", message.Target, message.Text),
		})
		s.scheduler.ScheduleEvent(currentBeat+1, SlotLogging, AgentEcho, auditPayload)
	}
}

// Helper function to check if a string contains a substring
func contains(s, substr string) bool {
	return strings.Contains(strings.ToLower(s), strings.ToLower(substr))
}
