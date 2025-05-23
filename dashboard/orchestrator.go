// ----------------------------------------------------------------------------
//  File:        orchestrator.go
//  Project:     Celaya Solutions (Agent Dashboard)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Orchestrates agent activity for parallel processing
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package main

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/rivo/tview"
)

// Orchestrator coordinates the activities of multiple agents
type Orchestrator struct {
	agents       []Agent
	apiClient    *APIClient
	logger       *Logger
	agentPanels  map[string]*tview.TextView
	app          *tview.Application
	outputView   *tview.TextView
	outputWriter *Writer
}

// NewOrchestrator creates a new orchestrator
func NewOrchestrator(
	agents []Agent,
	apiClient *APIClient,
	logger *Logger,
	agentPanels map[string]*tview.TextView,
	app *tview.Application,
	outputView *tview.TextView,
) *Orchestrator {
	return &Orchestrator{
		agents:       agents,
		apiClient:    apiClient,
		logger:       logger,
		agentPanels:  agentPanels,
		app:          app,
		outputView:   outputView,
		outputWriter: &Writer{TextView: outputView},
	}
}

// ProcessCommand processes a command in parallel across all agents
func (o *Orchestrator) ProcessCommand(ctx context.Context, command string) {
	// Log the command reception
	fmt.Fprintf(o.outputWriter, "[cyan]Processing command: %s[white]\n", command)

	// Create a wait group to wait for all agents to complete
	var wg sync.WaitGroup

	// Launch goroutines for each agent to process in parallel
	for _, agent := range o.agents {
		wg.Add(1)

		go func(agent Agent) {
			defer wg.Done()

			// Propagate cancellation from the parent context
			agentCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
			defer cancel()

			// Attempt to process the command with this agent
			o.processAgentCommand(agentCtx, agent, command)
		}(agent)
	}

	// Wait for all agents to complete
	wg.Wait()

	// Log completion
	fmt.Fprintf(o.outputWriter, "[green]All agents have processed the command[white]\n")
}

// processAgentCommand processes a command with a specific agent
func (o *Orchestrator) processAgentCommand(ctx context.Context, agent Agent, command string) {
	panel := o.agentPanels[agent.Name]
	if panel == nil {
		return
	}

	// Create a writer for the panel
	panelWriter := &Writer{TextView: panel}

	// Update the panel with the received command
	o.app.QueueUpdateDraw(func() {
		fmt.Fprintf(panelWriter, "[blue]%s [RECEIVED][white] Command: %s\n",
			time.Now().Format("15:04:05"), command)
		panel.ScrollToEnd()
	})

	// Log the action
	if err := o.logger.LogAgentAction(agent.Name, fmt.Sprintf("Received command: %s", command)); err != nil {
		o.app.QueueUpdateDraw(func() {
			fmt.Fprintf(panelWriter, "[red]%s [ERROR][white] Failed to log action: %v\n",
				time.Now().Format("15:04:05"), err)
			panel.ScrollToEnd()
		})
	}

	// Create the generate request
	req := &GenerateRequest{
		Model:  agent.Model,
		Prompt: fmt.Sprintf("Command from user: %s\n\nRespond as %s (%s).", command, agent.Name, agent.Role),
		System: agent.SystemPrompt,
		Stream: false,
	}

	// Call the agent API
	res, err := o.apiClient.Generate(ctx, agent.URL, req)
	if err != nil {
		// Handle error
		o.app.QueueUpdateDraw(func() {
			fmt.Fprintf(panelWriter, "[red]%s [ERROR][white] Failed to generate response: %v\n",
				time.Now().Format("15:04:05"), err)
			panel.ScrollToEnd()
		})

		// Log the error
		if logErr := o.logger.LogAgentError(agent.Name, fmt.Sprintf("API error: %v", err)); logErr != nil {
			fmt.Printf("Failed to log error: %v\n", logErr)
		}
		return
	}

	// Update the panel with the response
	o.app.QueueUpdateDraw(func() {
		fmt.Fprintf(panelWriter, "[green]%s [RESPONSE][white] %s\n",
			time.Now().Format("15:04:05"), res.Response)
		panel.ScrollToEnd()
	})

	// Log the response
	if err := o.logger.LogAgentResponse(agent.Name, res.Response); err != nil {
		o.app.QueueUpdateDraw(func() {
			fmt.Fprintf(panelWriter, "[red]%s [ERROR][white] Failed to log response: %v\n",
				time.Now().Format("15:04:05"), err)
			panel.ScrollToEnd()
		})
	}
}

// CheckAgentHealth checks the health of all agents
func (o *Orchestrator) CheckAgentHealth(ctx context.Context) map[string]bool {
	// Create a map to store health status
	healthStatus := make(map[string]bool, len(o.agents))

	// Create a wait group to wait for all health checks
	var wg sync.WaitGroup
	var mu sync.Mutex

	// Check each agent in parallel
	for _, agent := range o.agents {
		wg.Add(1)

		go func(agent Agent) {
			defer wg.Done()

			// Check health with timeout
			agentCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
			defer cancel()

			healthy, _ := o.apiClient.Health(agentCtx, agent.URL)

			// Store result
			mu.Lock()
			healthStatus[agent.Name] = healthy
			mu.Unlock()

			// Update panel
			panel := o.agentPanels[agent.Name]
			if panel != nil {
				panelWriter := &Writer{TextView: panel}
				o.app.QueueUpdateDraw(func() {
					if healthy {
						fmt.Fprintf(panelWriter, "[green]%s [HEALTH][white] Agent is healthy\n",
							time.Now().Format("15:04:05"))
					} else {
						fmt.Fprintf(panelWriter, "[red]%s [HEALTH][white] Agent is not responding\n",
							time.Now().Format("15:04:05"))
					}
					panel.ScrollToEnd()
				})
			}
		}(agent)
	}

	// Wait for all health checks
	wg.Wait()

	return healthStatus
}
