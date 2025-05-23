// ----------------------------------------------------------------------------
//  File:        simulator.go
//  Project:     Celaya Solutions (Celaya Beats)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: User interaction simulator with visualization for Celaya Beats
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	beats "github.com/celaya/celaya/celaya-beats"
)

func main() {
	// Parse command line flags
	beatDurationFlag := flag.Int("duration", 500, "Duration of each beat in milliseconds")
	noVisualsFlag := flag.Bool("no-visuals", false, "Disable visualization")
	flag.Parse()

	beatDuration := time.Duration(*beatDurationFlag) * time.Millisecond
	visualizationMode := !*noVisualsFlag

	fmt.Printf("Starting Celaya Beats Simulator with %v beat duration\n", beatDuration)
	fmt.Printf("Visualization: %v\n", visualizationMode)

	// Create context with cancellation
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle termination signals
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signalChan
		fmt.Println("\nReceived termination signal, shutting down...")
		cancel()
	}()

	// Create and configure the scheduler
	scheduler := beats.NewScheduler(beatDuration)

	// Define slot names
	scheduler.RegisterSlot(beats.SlotHousekeeping, "Housekeeping")
	scheduler.RegisterSlot(beats.SlotRouting, "Routing")
	scheduler.RegisterSlot(beats.SlotActions, "Actions")
	scheduler.RegisterSlot(beats.SlotLogging, "Logging")
	scheduler.RegisterSlot(beats.SlotPing, "Ping")

	// Create visual state tracker
	visualState := beats.NewVisualState(scheduler)

	// Create agents
	lyra := beats.NewLyraAgent(scheduler)
	otto := beats.NewOttoAgent(scheduler)
	arc := beats.NewArcAgent(scheduler)
	luma := beats.NewLumaAgent(scheduler)
	clarity := beats.NewClarityAgent(scheduler)
	echo := beats.NewEchoAgent(scheduler)

	// Start the scheduler and visualization
	scheduler.Start()
	visualState.Start()
	defer func() {
		scheduler.Stop()
		visualState.Stop()
	}()

	fmt.Println("Celaya Beats scheduler is running.")
	fmt.Println("Available agents:", lyra.ID(), otto.ID(), arc.ID(), luma.ID(), clarity.ID(), echo.ID())

	// Create user simulator
	simulator := beats.NewUserSimulator(scheduler, visualState)
	simulator.AddDefaultScenario()

	// Run the simulation
	fmt.Println("\nStarting simulation with a predefined user conversation...")
	fmt.Println("Each agent will process messages in its designated time slot.")
	fmt.Println("Press Ctrl+C to stop the simulation at any time.")
	fmt.Println("\n=============================================")

	// Allow time for the system to fully initialize
	time.Sleep(1 * time.Second)

	// Run the simulation
	simulator.RunSimulation(ctx, visualizationMode)

	// Give a moment to see the final state before exiting
	if ctx.Err() == nil {
		fmt.Println("\nSimulation completed successfully!")
		fmt.Println("Shutting down system...")
		time.Sleep(1 * time.Second)
	}
}
