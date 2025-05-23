// ----------------------------------------------------------------------------
//  File:        visualizer.go
//  Project:     Celaya Solutions (Celaya Beats)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Visualization of agent activities across Celaya Beats
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package beats

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"time"
)

// ActivityRecord represents a single activity of an agent
type ActivityRecord struct {
	Beat        Beat
	Slot        Slot
	Agent       AgentID
	Action      string
	Description string
	StartTime   time.Time
	EndTime     time.Time
	Status      string
}

// VisualState tracks what all agents are doing at any given beat
type VisualState struct {
	scheduler     *Scheduler
	activityLog   map[Beat]map[AgentID][]ActivityRecord
	activeAgents  map[AgentID]bool
	activityMutex sync.RWMutex
	ctx           context.Context
	cancel        context.CancelFunc
	notifications chan struct{}
}

// NewVisualState creates a new visualization state tracker
func NewVisualState(scheduler *Scheduler) *VisualState {
	ctx, cancel := context.WithCancel(context.Background())
	return &VisualState{
		scheduler:     scheduler,
		activityLog:   make(map[Beat]map[AgentID][]ActivityRecord),
		activeAgents:  make(map[AgentID]bool),
		ctx:           ctx,
		cancel:        cancel,
		notifications: make(chan struct{}, 10),
	}
}

// Start begins monitoring agent activities
func (v *VisualState) Start() {
	// Listen for beat triggers from the scheduler
	go v.monitorBeats()
}

// Stop halts the visualization monitoring
func (v *VisualState) Stop() {
	v.cancel()
}

// monitorBeats listens for beat completions and updates the visualization
func (v *VisualState) monitorBeats() {
	for {
		select {
		case <-v.ctx.Done():
			return
		case beat := <-v.scheduler.beatTrigger:
			v.updateVisualization(beat)
			// Notify any listeners that the visualization has been updated
			select {
			case v.notifications <- struct{}{}:
			default:
				// Channel full, drop notification
			}
		}
	}
}

// RegisterActivity records an agent's activity
func (v *VisualState) RegisterActivity(record ActivityRecord) {
	v.activityMutex.Lock()
	defer v.activityMutex.Unlock()

	// Initialize maps if they don't exist
	if _, exists := v.activityLog[record.Beat]; !exists {
		v.activityLog[record.Beat] = make(map[AgentID][]ActivityRecord)
	}

	if _, exists := v.activityLog[record.Beat][record.Agent]; !exists {
		v.activityLog[record.Beat][record.Agent] = []ActivityRecord{}
	}

	// Mark this agent as active
	v.activeAgents[record.Agent] = true

	// Add the activity record
	v.activityLog[record.Beat][record.Agent] = append(
		v.activityLog[record.Beat][record.Agent], record)
}

// updateVisualization refreshes the visualization after a beat completes
func (v *VisualState) updateVisualization(beat Beat) {
	// Collect events from this beat and convert to activity records
	events := v.scheduler.FetchEvents(beat)

	for _, event := range events {
		action := "Unknown"
		description := "Unknown activity"

		if payload, ok := event.Payload.(ActionPayload); ok {
			action = string(payload.Type)

			// Generate a human-readable description based on the action type
			switch payload.Type {
			case ActionHealthCheck:
				description = "Performing system health check"
			case ActionRouteMessage:
				description = "Routing messages between agents"
			case ActionStartVehicle:
				if data, ok := payload.Data.(map[string]interface{}); ok {
					mode, _ := data["mode"].(string)
					temp, _ := data["temp"].(string)
					description = fmt.Sprintf("Starting vehicle: mode=%s, temp=%s", mode, temp)
				} else {
					description = "Starting vehicle with default settings"
				}
			case ActionLogEvent:
				if data, ok := payload.Data.(map[string]interface{}); ok {
					message, _ := data["message"].(string)
					description = fmt.Sprintf("Logging: %s", message)
				} else {
					description = "Logging event"
				}
			case ActionAuditEvent:
				description = "Auditing system activity"
			}
		}

		// Create and register the activity record
		record := ActivityRecord{
			Beat:        beat,
			Slot:        event.Slot,
			Agent:       event.Agent,
			Action:      action,
			Description: description,
			StartTime:   v.scheduler.BeatToTime(beat),
			EndTime:     v.scheduler.BeatToTime(beat + 1),
			Status:      "Completed",
		}

		v.RegisterActivity(record)
	}
}

// GetActiveAgents returns a list of all active agents
func (v *VisualState) GetActiveAgents() []AgentID {
	v.activityMutex.RLock()
	defer v.activityMutex.RUnlock()

	agents := make([]AgentID, 0, len(v.activeAgents))
	for agent := range v.activeAgents {
		agents = append(agents, agent)
	}
	return agents
}

// GetAgentActivities returns all activities for an agent at a specific beat
func (v *VisualState) GetAgentActivities(beat Beat, agent AgentID) []ActivityRecord {
	v.activityMutex.RLock()
	defer v.activityMutex.RUnlock()

	if beatMap, exists := v.activityLog[beat]; exists {
		if activities, exists := beatMap[agent]; exists {
			return activities
		}
	}

	return []ActivityRecord{}
}

// GetBeatActivities returns all activities for all agents at a specific beat
func (v *VisualState) GetBeatActivities(beat Beat) map[AgentID][]ActivityRecord {
	v.activityMutex.RLock()
	defer v.activityMutex.RUnlock()

	if beatMap, exists := v.activityLog[beat]; exists {
		// Create a deep copy to avoid concurrent access issues
		result := make(map[AgentID][]ActivityRecord)
		for agent, activities := range beatMap {
			result[agent] = append([]ActivityRecord{}, activities...)
		}
		return result
	}

	return map[AgentID][]ActivityRecord{}
}

// FormatBeatVisualization returns a formatted string representation of all agent activities at a beat
func (v *VisualState) FormatBeatVisualization(beat Beat) string {
	activities := v.GetBeatActivities(beat)
	agents := v.GetActiveAgents()

	if len(activities) == 0 {
		return fmt.Sprintf("Beat %d: No agent activities\n", beat)
	}

	var builder strings.Builder

	// Header with beat information
	builder.WriteString(fmt.Sprintf("================ BEAT %d ================\n", beat))
	builder.WriteString(fmt.Sprintf("Time: %s\n\n", v.scheduler.BeatToTime(beat).Format(time.RFC3339)))

	// List each agent's activities
	for _, agent := range agents {
		agentActivities, exists := activities[agent]
		if !exists || len(agentActivities) == 0 {
			builder.WriteString(fmt.Sprintf("%-8s │ IDLE\n", agent))
			continue
		}

		// Show what the agent is doing
		for i, activity := range agentActivities {
			if i == 0 {
				builder.WriteString(fmt.Sprintf("%-8s │ %s [%s] (Slot %d)\n",
					agent, activity.Description, activity.Action, activity.Slot))
			} else {
				builder.WriteString(fmt.Sprintf("%-8s │  └─ %s\n",
					"", activity.Description))
			}
		}
	}

	builder.WriteString("\n")
	return builder.String()
}

// FormatTimelineVisualization returns a visualization of agent activities over a range of beats
func (v *VisualState) FormatTimelineVisualization(startBeat, endBeat Beat) string {
	if startBeat > endBeat {
		return "Invalid beat range\n"
	}

	var builder strings.Builder
	builder.WriteString(fmt.Sprintf("TIMELINE FROM BEAT %d TO %d\n\n", startBeat, endBeat))

	for beat := startBeat; beat <= endBeat; beat++ {
		builder.WriteString(v.FormatBeatVisualization(beat))
	}

	return builder.String()
}

// WaitForUpdate waits for the next visualization update or context cancellation
func (v *VisualState) WaitForUpdate(ctx context.Context) bool {
	select {
	case <-ctx.Done():
		return false
	case <-v.notifications:
		return true
	}
}
