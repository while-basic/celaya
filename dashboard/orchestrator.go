// ----------------------------------------------------------------------------
//  File:        orchestrator.go
//  Project:     Celaya Solutions (Agent Dashboard)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Orchestrator for coordinating agent activities
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

	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

// Orchestrator coordinates activities among multiple agents
type Orchestrator struct {
	Agents       []Agent
	API          *APIClient
	Logger       *Logger
	AgentPanels  map[string]*tview.TextView
	App          *tview.Application
	OutputView   *tview.TextView
	ActiveAgents map[string]bool
	mu           sync.Mutex
}

// NewOrchestrator creates a new orchestrator instance
func NewOrchestrator(
	agents []Agent,
	api *APIClient,
	logger *Logger,
	panels map[string]*tview.TextView,
	app *tview.Application,
	output *tview.TextView,
) *Orchestrator {
	return &Orchestrator{
		Agents:       agents,
		API:          api,
		Logger:       logger,
		AgentPanels:  panels,
		App:          app,
		OutputView:   output,
		ActiveAgents: make(map[string]bool),
	}
}

// ProcessCommand sends a command to all agents
func (o *Orchestrator) ProcessCommand(ctx context.Context, command string) {
	var wg sync.WaitGroup

	// Process the command for each agent
	for _, agent := range o.Agents {
		wg.Add(1)
		go func(a Agent) {
			defer wg.Done()
			o.sendCommandToAgent(ctx, command, a)
		}(agent)
	}

	// Wait for all agents to process the command
	go func() {
		wg.Wait()
		o.logToOutput("[cyan]All agents have processed the command.[white]\n")
	}()
}

// ProcessCommandForAgents sends a command to a specific set of agents
func (o *Orchestrator) ProcessCommandForAgents(ctx context.Context, command string, agents []Agent) {
	if len(agents) == 0 {
		o.logToOutput("[yellow]No agents specified for command.[white]\n")
		return
	}

	var wg sync.WaitGroup

	// Process the command for each specified agent
	for _, agent := range agents {
		wg.Add(1)
		go func(a Agent) {
			defer wg.Done()
			o.sendCommandToAgent(ctx, command, a)
		}(agent)
	}

	// Wait for all agents to process the command
	go func() {
		wg.Wait()
		o.logToOutput(fmt.Sprintf("[cyan]Command processed by %d agents.[white]\n", len(agents)))
	}()
}

// ProcessDirectMessage sends a direct message to a specific agent
func (o *Orchestrator) ProcessDirectMessage(ctx context.Context, message string, agent Agent) {
	// Log the direct message in the agent's panel
	panel := o.AgentPanels[agent.Name]
	if panel != nil {
		o.App.QueueUpdateDraw(func() {
			fmt.Fprintf(panel, "[magenta]%s [DIRECT MESSAGE][white] %s\n",
				time.Now().Format("15:04:05"), message)
			panel.ScrollToEnd()
		})
	}

	// Send the command to the agent
	o.sendCommandToAgent(ctx, message, agent)
}

// sendCommandToAgent sends a command to a specific agent
func (o *Orchestrator) sendCommandToAgent(ctx context.Context, command string, agent Agent) {
	// Log the action
	o.logAgentAction(agent.Name, command)

	// Update the agent panel with the command
	panel := o.AgentPanels[agent.Name]
	if panel != nil {
		o.App.QueueUpdateDraw(func() {
			fmt.Fprintf(panel, "[yellow]%s [COMMAND][white] %s\n",
				time.Now().Format("15:04:05"), command)
			panel.ScrollToEnd()
		})
	}

	// If the agent is not active, show a message and return
	if !o.isAgentActive(agent.Name) {
		response := fmt.Sprintf("Error: Agent '%s' is not currently active. Please check health.", agent.Name)
		o.logAgentResponse(agent.Name, response)

		if panel != nil {
			o.App.QueueUpdateDraw(func() {
				fmt.Fprintf(panel, "[red]%s [ERROR][white] %s\n",
					time.Now().Format("15:04:05"), response)
				panel.ScrollToEnd()
			})
		}
		return
	}

	// Send the command to the agent via API
	response, err := o.sendAgentCommand(ctx, agent, command)
	if err != nil {
		errMsg := fmt.Sprintf("Error: %v", err)
		o.logAgentResponse(agent.Name, errMsg)

		if panel != nil {
			o.App.QueueUpdateDraw(func() {
				fmt.Fprintf(panel, "[red]%s [ERROR][white] %s\n",
					time.Now().Format("15:04:05"), errMsg)
				panel.ScrollToEnd()
			})
		}
		return
	}

	// Log the response
	o.logAgentResponse(agent.Name, response)

	// Update the agent panel with the response
	if panel != nil {
		o.App.QueueUpdateDraw(func() {
			fmt.Fprintf(panel, "[green]%s [RESPONSE][white] %s\n",
				time.Now().Format("15:04:05"), response)
			panel.ScrollToEnd()
		})
	}
}

// sendAgentCommand sends a command to an agent via the API
func (o *Orchestrator) sendAgentCommand(ctx context.Context, agent Agent, command string) (string, error) {
	// Log the command
	o.Logger.LogInfo(agent.Name, fmt.Sprintf("Sending command: %s", command))

	// Send the command to the agent via API
	return o.API.SendCommand(ctx, agent, command)
}

// logAgentAction logs an agent action
func (o *Orchestrator) logAgentAction(agentName, action string) {
	o.Logger.LogInfo(agentName, fmt.Sprintf("Action: %s", action))
}

// logAgentResponse logs an agent response
func (o *Orchestrator) logAgentResponse(agentName, response string) {
	o.Logger.LogInfo(agentName, fmt.Sprintf("Response: %s", response))
}

// CheckAgentHealth checks the health of all agents
func (o *Orchestrator) CheckAgentHealth(ctx context.Context) {
	var wg sync.WaitGroup

	// Check the health of each agent
	for _, agent := range o.Agents {
		wg.Add(1)
		go func(a Agent) {
			defer wg.Done()

			panel := o.AgentPanels[a.Name]
			if panel == nil {
				return
			}

			// Update the panel with the health check
			o.App.QueueUpdateDraw(func() {
				fmt.Fprintf(panel, "[yellow]%s [HEALTH CHECK][white] Checking agent health...\n",
					time.Now().Format("15:04:05"))
				panel.ScrollToEnd()
			})

			// Check the agent's health via API
			healthy, err := o.API.CheckHealth(ctx, a)

			if err != nil || !healthy {
				errorMsg := "Agent is not responding"
				if err != nil {
					errorMsg = fmt.Sprintf("Health check failed: %v", err)
				}

				o.setAgentActive(a.Name, false)

				// Log the health check error
				o.Logger.LogInfo(a.Name, errorMsg)

				// Update the panel with the health check error
				o.App.QueueUpdateDraw(func() {
					fmt.Fprintf(panel, "[red]%s [HEALTH ERROR][white] %s\n",
						time.Now().Format("15:04:05"), errorMsg)
					panel.SetBorderColor(tcell.ColorRed)
					panel.ScrollToEnd()
				})

				// Log to main output
				o.logToOutput(fmt.Sprintf("[red]%s is not healthy: %s[white]\n", a.Name, errorMsg))
			} else {
				o.setAgentActive(a.Name, true)

				// Log the health check success
				o.Logger.LogInfo(a.Name, "Agent is healthy")

				// Update the panel with the health check success
				o.App.QueueUpdateDraw(func() {
					fmt.Fprintf(panel, "[green]%s [HEALTH OK][white] Agent is healthy\n",
						time.Now().Format("15:04:05"))
					panel.SetBorderColor(tcell.ColorBlue)
					panel.ScrollToEnd()
				})

				// Log to main output
				o.logToOutput(fmt.Sprintf("[green]%s is healthy[white]\n", a.Name))
			}
		}(agent)
	}

	// Wait for all health checks to complete
	go func() {
		wg.Wait()
		o.logToOutput("[cyan]Health check completed for all agents.[white]\n")
	}()
}

// isAgentActive checks if an agent is active
func (o *Orchestrator) isAgentActive(agentName string) bool {
	o.mu.Lock()
	defer o.mu.Unlock()

	// If the agent doesn't exist in the map, assume it's active
	// This is to allow commands before a health check has been run
	if _, exists := o.ActiveAgents[agentName]; !exists {
		return true
	}

	return o.ActiveAgents[agentName]
}

// setAgentActive sets an agent's active status
func (o *Orchestrator) setAgentActive(agentName string, active bool) {
	o.mu.Lock()
	defer o.mu.Unlock()

	o.ActiveAgents[agentName] = active
}

// logToOutput logs a message to the main output view
func (o *Orchestrator) logToOutput(message string) {
	o.App.QueueUpdateDraw(func() {
		fmt.Fprint(o.OutputView, message)
		o.OutputView.ScrollToEnd()
	})
}
