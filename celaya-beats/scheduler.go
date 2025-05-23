// ----------------------------------------------------------------------------
//  File:        scheduler.go
//  Project:     Celaya Solutions (Celaya Beats)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Core scheduler implementation for the Celaya Beats system
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package beats

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Slot represents a specific execution window within a Beat
type Slot int

// Beat (or Tick) represents a specific point in time within the scheduler
type Beat int64

// AgentID is a unique identifier for an agent
type AgentID string

// Event represents a scheduled action to be executed by an agent
type Event struct {
	Beat      Beat      `json:"beat"`
	Slot      Slot      `json:"slot"`
	Agent     AgentID   `json:"agent"`
	Payload   any       `json:"payload"`
	Timestamp time.Time `json:"timestamp"`
}

// EventCallback is a function that executes when an event is triggered
type EventCallback func(context.Context, Event) error

// Scheduler is the main component responsible for coordinating the Celaya Beat system
type Scheduler struct {
	beatDuration time.Duration
	startTime    time.Time
	currentBeat  Beat
	timeline     map[Beat][]Event
	slots        map[Slot]string
	agents       map[AgentID]EventCallback
	mu           sync.RWMutex
	ctx          context.Context
	cancel       context.CancelFunc
	beatTrigger  chan Beat
	wg           sync.WaitGroup
}

// NewScheduler creates a new Celaya Beat scheduler
func NewScheduler(beatDuration time.Duration) *Scheduler {
	ctx, cancel := context.WithCancel(context.Background())
	return &Scheduler{
		beatDuration: beatDuration,
		timeline:     make(map[Beat][]Event),
		slots:        make(map[Slot]string),
		agents:       make(map[AgentID]EventCallback),
		ctx:          ctx,
		cancel:       cancel,
		beatTrigger:  make(chan Beat, 10), // Buffer for beat triggers
	}
}

// RegisterSlot assigns a name to a specific slot number
func (s *Scheduler) RegisterSlot(slot Slot, name string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.slots[slot] = name
}

// RegisterAgent registers a new agent with the scheduler
func (s *Scheduler) RegisterAgent(id AgentID, callback EventCallback) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.agents[id] = callback
}

// ScheduleEvent adds a new event to the timeline
func (s *Scheduler) ScheduleEvent(beat Beat, slot Slot, agent AgentID, payload any) Event {
	s.mu.Lock()
	defer s.mu.Unlock()

	event := Event{
		Beat:      beat,
		Slot:      slot,
		Agent:     agent,
		Payload:   payload,
		Timestamp: time.Now(),
	}

	if _, exists := s.timeline[beat]; !exists {
		s.timeline[beat] = []Event{}
	}
	s.timeline[beat] = append(s.timeline[beat], event)
	return event
}

// Start begins the scheduler and sets the start time
func (s *Scheduler) Start() {
	s.mu.Lock()
	s.startTime = time.Now()
	s.currentBeat = 0
	s.mu.Unlock()

	s.wg.Add(1)
	go s.mainLoop()
}

// Stop halts the scheduler execution
func (s *Scheduler) Stop() {
	s.cancel()
	s.wg.Wait()
}

// mainLoop is the core loop that processes beats at regular intervals
func (s *Scheduler) mainLoop() {
	defer s.wg.Done()

	ticker := time.NewTicker(s.beatDuration)
	defer ticker.Stop()

	for {
		select {
		case <-s.ctx.Done():
			return
		case <-ticker.C:
			s.mu.Lock()
			beat := s.currentBeat
			s.currentBeat++
			s.mu.Unlock()

			// Process the beat in a separate goroutine
			s.wg.Add(1)
			go func(b Beat) {
				defer s.wg.Done()
				s.processBeat(b)
				// Notify any listeners about the completed beat
				select {
				case s.beatTrigger <- b:
				default:
					// Channel is full, beat notification is dropped
				}
			}(beat)
		}
	}
}

// processBeat handles all events scheduled for a specific beat
func (s *Scheduler) processBeat(beat Beat) {
	// Create a context with timeout for this beat
	ctx, cancel := context.WithTimeout(s.ctx, s.beatDuration)
	defer cancel()

	// Get events for this beat
	s.mu.RLock()
	events, exists := s.timeline[beat]
	s.mu.RUnlock()

	if !exists {
		return
	}

	// Process events by slot in order
	slots := make(map[Slot][]Event)
	for _, event := range events {
		slots[event.Slot] = append(slots[event.Slot], event)
	}

	// Process slots in ascending order
	for slot := Slot(0); slot < Slot(5); slot++ {
		slotEvents, hasSlot := slots[slot]
		if !hasSlot {
			continue
		}

		// Process all events in this slot
		for _, event := range slotEvents {
			s.mu.RLock()
			callback, hasAgent := s.agents[event.Agent]
			s.mu.RUnlock()

			if hasAgent {
				// Execute agent callback (in same goroutine for sequential execution)
				err := callback(ctx, event)
				if err != nil {
					fmt.Printf("Error processing event: %v\n", err)
				}
			}
		}
	}
}

// TimeToBeat converts a time.Time to a Beat
func (s *Scheduler) TimeToBeat(t time.Time) Beat {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return Beat(t.Sub(s.startTime) / s.beatDuration)
}

// BeatToTime converts a Beat to a time.Time
func (s *Scheduler) BeatToTime(beat Beat) time.Time {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.startTime.Add(time.Duration(beat) * s.beatDuration)
}

// CurrentBeat returns the current beat number
func (s *Scheduler) CurrentBeat() Beat {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.currentBeat
}

// FetchEvents retrieves all events for a specific beat
func (s *Scheduler) FetchEvents(beat Beat) []Event {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.timeline[beat]
}
