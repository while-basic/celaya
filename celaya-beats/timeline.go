// ----------------------------------------------------------------------------
//  File:        timeline.go
//  Project:     Celaya Solutions (Celaya Beats)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Timeline viewer for the Celaya Beats scheduler
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package beats

import (
	"fmt"
	"sort"
	"strings"
	"time"
)

// TimelineViewer provides a readable view of the event timeline
type TimelineViewer struct {
	scheduler *Scheduler
}

// NewTimelineViewer creates a new timeline viewer
func NewTimelineViewer(scheduler *Scheduler) *TimelineViewer {
	return &TimelineViewer{
		scheduler: scheduler,
	}
}

// EventSummary provides a summary of an event
type EventSummary struct {
	Beat      Beat
	Slot      Slot
	SlotName  string
	Agent     AgentID
	Action    string
	Timestamp time.Time
}

// GetEventsAtBeat returns all events at a specific beat
func (v *TimelineViewer) GetEventsAtBeat(beat Beat) []EventSummary {
	events := v.scheduler.FetchEvents(beat)
	summaries := make([]EventSummary, 0, len(events))

	for _, event := range events {
		action := "Unknown"
		if payload, ok := event.Payload.(ActionPayload); ok {
			action = string(payload.Type)
		}

		slotName := fmt.Sprintf("Slot %d", event.Slot)
		if name, ok := v.scheduler.slots[event.Slot]; ok {
			slotName = name
		}

		summaries = append(summaries, EventSummary{
			Beat:      event.Beat,
			Slot:      event.Slot,
			SlotName:  slotName,
			Agent:     event.Agent,
			Action:    action,
			Timestamp: event.Timestamp,
		})
	}

	// Sort by slot for consistent ordering
	sort.Slice(summaries, func(i, j int) bool {
		return summaries[i].Slot < summaries[j].Slot
	})

	return summaries
}

// GetEventsForTimeRange returns events within a time range
func (v *TimelineViewer) GetEventsForTimeRange(startTime, endTime time.Time) map[Beat][]EventSummary {
	startBeat := v.scheduler.TimeToBeat(startTime)
	endBeat := v.scheduler.TimeToBeat(endTime)

	result := make(map[Beat][]EventSummary)
	for beat := startBeat; beat <= endBeat; beat++ {
		events := v.GetEventsAtBeat(beat)
		if len(events) > 0 {
			result[beat] = events
		}
	}

	return result
}

// FormatEventsAtBeat returns a formatted string representation of events at a beat
func (v *TimelineViewer) FormatEventsAtBeat(beat Beat) string {
	events := v.GetEventsAtBeat(beat)
	if len(events) == 0 {
		return fmt.Sprintf("No events at beat %d\n", beat)
	}

	var builder strings.Builder
	builder.WriteString(fmt.Sprintf("Events at beat %d (Time: %s):\n",
		beat, v.scheduler.BeatToTime(beat).Format(time.RFC3339)))

	for _, event := range events {
		builder.WriteString(fmt.Sprintf("  [%s] Agent: %s, Action: %s\n",
			event.SlotName, event.Agent, event.Action))
	}

	return builder.String()
}

// FormatTimeRange returns a formatted string representation of events in a time range
func (v *TimelineViewer) FormatTimeRange(startTime, endTime time.Time) string {
	eventsMap := v.GetEventsForTimeRange(startTime, endTime)
	if len(eventsMap) == 0 {
		return "No events in the specified time range.\n"
	}

	var builder strings.Builder
	builder.WriteString(fmt.Sprintf("Events from %s to %s:\n",
		startTime.Format(time.RFC3339), endTime.Format(time.RFC3339)))

	// Get the beats in ascending order
	beats := make([]Beat, 0, len(eventsMap))
	for beat := range eventsMap {
		beats = append(beats, beat)
	}
	sort.Slice(beats, func(i, j int) bool {
		return beats[i] < beats[j]
	})

	// Print events for each beat
	for _, beat := range beats {
		events := eventsMap[beat]
		builder.WriteString(fmt.Sprintf("\nBeat %d (Time: %s):\n",
			beat, v.scheduler.BeatToTime(beat).Format(time.RFC3339)))

		for _, event := range events {
			builder.WriteString(fmt.Sprintf("  [%s] Agent: %s, Action: %s\n",
				event.SlotName, event.Agent, event.Action))
		}
	}

	return builder.String()
}

// FormatNoonToday returns a formatted string representation of events at noon today
func (v *TimelineViewer) FormatNoonToday() string {
	now := time.Now()
	noon := time.Date(now.Year(), now.Month(), now.Day(), 12, 0, 0, 0, now.Location())

	if noon.After(now) {
		return "Noon today hasn't occurred yet.\n"
	}

	noonBeat := v.scheduler.TimeToBeat(noon)
	return v.FormatEventsAtBeat(noonBeat)
}
