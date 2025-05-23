// ----------------------------------------------------------------------------
//  File:        main.go
//  Project:     Celaya Solutions (Celaya Beats)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: CLI driver program for the Celaya Beats scheduling system
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	beats "github.com/celaya/celaya/celaya-beats"
)

const (
	defaultBeatDuration = 500 * time.Millisecond
)

func main() {
	// Parse command line flags
	beatDurationFlag := flag.Int("duration", 500, "Duration of each beat in milliseconds")
	demoFlag := flag.Bool("demo", false, "Run in demo mode with predefined events")
	flag.Parse()

	beatDuration := time.Duration(*beatDurationFlag) * time.Millisecond
	fmt.Printf("Starting Celaya Beats scheduler with %v beat duration\n", beatDuration)

	// Create and configure the scheduler
	scheduler := beats.NewScheduler(beatDuration)

	// Define slot names
	scheduler.RegisterSlot(beats.SlotHousekeeping, "Housekeeping")
	scheduler.RegisterSlot(beats.SlotRouting, "Routing")
	scheduler.RegisterSlot(beats.SlotActions, "Actions")
	scheduler.RegisterSlot(beats.SlotLogging, "Logging")
	scheduler.RegisterSlot(beats.SlotPing, "Ping")

	// Create agents
	lyra := beats.NewLyraAgent(scheduler)
	arc := beats.NewArcAgent(scheduler)
	clarity := beats.NewClarityAgent(scheduler)

	// Create the timeline viewer
	viewer := beats.NewTimelineViewer(scheduler)

	// Start the scheduler
	scheduler.Start()
	defer scheduler.Stop()

	fmt.Println("Celaya Beats scheduler is running.")
	fmt.Println("Available agents:", lyra.ID(), arc.ID(), clarity.ID())

	// Schedule some initial events if in demo mode
	if *demoFlag {
		runDemo(scheduler)
	}

	// Start the command-line interface
	fmt.Println("\nCommand-line interface is ready. Type 'help' for commands.")
	runCLI(scheduler, viewer)
}

// runDemo schedules a series of demo events
func runDemo(scheduler *beats.Scheduler) {
	fmt.Println("Running in demo mode with predefined events...")

	// Schedule health check for Lyra at beat 5
	healthCheckPayload := beats.NewActionPayload(beats.ActionHealthCheck, nil)
	scheduler.ScheduleEvent(5, beats.SlotHousekeeping, beats.AgentLyra, healthCheckPayload)
	fmt.Println("Scheduled Lyra health check at beat 5")

	// Schedule vehicle start for Arc at beat 10
	vehiclePayload := beats.NewActionPayload(beats.ActionStartVehicle, map[string]interface{}{
		"mode": "cool",
		"temp": "68°F",
	})
	scheduler.ScheduleEvent(10, beats.SlotActions, beats.AgentArc, vehiclePayload)
	fmt.Println("Scheduled Arc vehicle start at beat 10")

	// Schedule another vehicle action for beat 15
	vehiclePayload2 := beats.NewActionPayload(beats.ActionStartVehicle, map[string]interface{}{
		"mode": "heat",
		"temp": "72°F",
	})
	scheduler.ScheduleEvent(15, beats.SlotActions, beats.AgentArc, vehiclePayload2)
	fmt.Println("Scheduled Arc vehicle update at beat 15")
}

// runCLI runs the interactive command line interface
func runCLI(scheduler *beats.Scheduler, viewer *beats.TimelineViewer) {
	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Print("> ")
		if !scanner.Scan() {
			break
		}

		line := scanner.Text()
		parts := strings.Fields(line)
		if len(parts) == 0 {
			continue
		}

		command := parts[0]

		switch command {
		case "help":
			fmt.Println("Available commands:")
			fmt.Println("  status             - Show current beat and scheduler status")
			fmt.Println("  events [beat]      - Show events at the specified beat")
			fmt.Println("  schedule [beat] [agent] [action] - Schedule a new event")
			fmt.Println("  lyra [beat]        - Schedule a Lyra health check")
			fmt.Println("  arc [beat] [mode] [temp] - Schedule an Arc vehicle start")
			fmt.Println("  now                - Show current beat time")
			fmt.Println("  noon               - Show events at noon today")
			fmt.Println("  quit               - Exit the program")

		case "status":
			currentBeat := scheduler.CurrentBeat()
			fmt.Printf("Current beat: %d (Time: %s)\n",
				currentBeat, scheduler.BeatToTime(currentBeat).Format(time.RFC3339))

		case "events":
			var beat beats.Beat
			if len(parts) > 1 {
				fmt.Sscanf(parts[1], "%d", &beat)
			} else {
				beat = scheduler.CurrentBeat() - 1 // Last completed beat
			}
			fmt.Println(viewer.FormatEventsAtBeat(beat))

		case "schedule":
			if len(parts) < 4 {
				fmt.Println("Usage: schedule [beat] [agent] [action]")
				continue
			}

			var beat beats.Beat
			fmt.Sscanf(parts[1], "%d", &beat)
			agent := beats.AgentID(parts[2])
			action := beats.ActionType(parts[3])

			// Simple payload for demonstration
			payload := beats.NewActionPayload(action, nil)
			event := scheduler.ScheduleEvent(beat, beats.SlotActions, agent, payload)
			fmt.Printf("Scheduled event: Beat %d, Agent %s, Action %s\n",
				event.Beat, event.Agent, action)

		case "lyra":
			if len(parts) < 2 {
				fmt.Println("Usage: lyra [beat]")
				continue
			}

			var beat beats.Beat
			fmt.Sscanf(parts[1], "%d", &beat)

			healthCheckPayload := beats.NewActionPayload(beats.ActionHealthCheck, nil)
			event := scheduler.ScheduleEvent(beat, beats.SlotHousekeeping, beats.AgentLyra, healthCheckPayload)
			fmt.Printf("Scheduled Lyra health check at beat %d\n", event.Beat)

		case "arc":
			if len(parts) < 4 {
				fmt.Println("Usage: arc [beat] [mode] [temp]")
				continue
			}

			var beat beats.Beat
			fmt.Sscanf(parts[1], "%d", &beat)
			mode := parts[2]
			temp := parts[3]

			vehiclePayload := beats.NewActionPayload(beats.ActionStartVehicle, map[string]interface{}{
				"mode": mode,
				"temp": temp,
			})
			event := scheduler.ScheduleEvent(beat, beats.SlotActions, beats.AgentArc, vehiclePayload)
			fmt.Printf("Scheduled Arc vehicle action at beat %d: mode=%s, temp=%s\n",
				event.Beat, mode, temp)

		case "now":
			currentBeat := scheduler.CurrentBeat()
			fmt.Printf("Current beat: %d (Time: %s)\n",
				currentBeat, scheduler.BeatToTime(currentBeat).Format(time.RFC3339))

		case "noon":
			fmt.Println(viewer.FormatNoonToday())

		case "quit", "exit":
			fmt.Println("Exiting Celaya Beats scheduler.")
			return

		default:
			fmt.Println("Unknown command. Type 'help' for available commands.")
		}
	}
}
