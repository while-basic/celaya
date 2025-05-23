// ----------------------------------------------------------------------------
//  File:        main.go
//  Project:     Celaya Solutions (Agent Dashboard)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Main entry point for the agent dashboard application
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

// Agent represents a single agent instance
type Agent struct {
	Name         string `json:"name"`
	URL          string `json:"url"`
	Model        string `json:"model"`
	SystemPrompt string `json:"system_prompt"`
	Role         string `json:"role"`
	LogFile      string
	Group        string `json:"group,omitempty"`
}

// AgentConfig represents the configuration for all agents
type AgentConfig struct {
	Agents    []Agent                `json:"agents"`
	Settings  map[string]interface{} `json:"settings"`
	Groups    map[string][]string    `json:"groups,omitempty"`
	Templates map[string]string      `json:"templates,omitempty"`
}

// LogEntry represents a single log entry from an agent
type LogEntry struct {
	Timestamp time.Time `json:"timestamp"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
	Agent     string    `json:"agent"`
	Action    string    `json:"action,omitempty"`
	Response  string    `json:"response,omitempty"`
}

// CommandTemplate represents a saved command template
type CommandTemplate struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Command     string `json:"command"`
}

var (
	configPath = flag.String("config", "config.json", "Path to agent configuration file")
	logPath    = flag.String("logpath", "logs", "Path to agent log directory")
	timeoutSec = flag.Int("timeout", 60, "API timeout in seconds")
	jsonLogs   = flag.Bool("json", true, "Format logs as JSON")
)

// loadAgentConfig loads the agent configuration from a JSON file
func loadAgentConfig(path string) (*AgentConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var config AgentConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, err
	}

	// Initialize groups if not present
	if config.Groups == nil {
		config.Groups = make(map[string][]string)

		// Create default groups based on roles
		roleGroups := make(map[string][]string)
		for _, agent := range config.Agents {
			if agent.Role != "" {
				roleGroups[agent.Role] = append(roleGroups[agent.Role], agent.Name)
			}
		}

		// Add role-based groups
		for role, members := range roleGroups {
			config.Groups[role] = members
		}
	}

	// Initialize templates if not present
	if config.Templates == nil {
		config.Templates = map[string]string{
			"intro":     "Please introduce yourself and your role briefly.",
			"analyze":   "Please analyze the following situation: [SITUATION]",
			"summarize": "Summarize the key points of this discussion so far.",
			"plan":      "Create a step-by-step plan to address: [TOPIC]",
		}
	}

	return &config, nil
}

// Writer is a simple wrapper around tview.TextView to implement io.Writer
type Writer struct {
	TextView *tview.TextView
}

// Write implements io.Writer
func (w *Writer) Write(p []byte) (n int, err error) {
	w.TextView.Write(p)
	return len(p), nil
}

// Dashboard holds the state of the dashboard application
type Dashboard struct {
	Config         *AgentConfig
	AgentPanels    map[string]*tview.TextView
	OutputView     *tview.TextView
	OutputWriter   *Writer
	App            *tview.Application
	Orchestrator   *Orchestrator
	FocusedAgents  map[string]bool
	CommandHistory []string
	HistoryPos     int
}

// NewDashboard creates a new dashboard instance
func NewDashboard(config *AgentConfig) *Dashboard {
	return &Dashboard{
		Config:         config,
		AgentPanels:    make(map[string]*tview.TextView),
		FocusedAgents:  make(map[string]bool),
		CommandHistory: make([]string, 0, 100),
		HistoryPos:     -1,
	}
}

// ProcessCommand processes a command entered by the user
func (d *Dashboard) ProcessCommand(ctx context.Context, cmdStr string) {
	// Save command to history
	d.CommandHistory = append(d.CommandHistory, cmdStr)
	d.HistoryPos = len(d.CommandHistory)

	// Split command and arguments
	parts := strings.Fields(cmdStr)
	if len(parts) == 0 {
		return
	}

	cmd := strings.ToLower(parts[0])
	args := parts[1:]

	// Special commands
	switch cmd {
	case "quit", "exit":
		d.App.Stop()
		return

	case "health":
		fmt.Fprintf(d.OutputWriter, "[yellow]Checking agent health...[white]\n")
		go d.Orchestrator.CheckAgentHealth(ctx)
		return

	case "help":
		d.showHelp()
		return

	case "focus":
		d.handleFocusCommand(args)
		return

	case "unfocus":
		d.handleUnfocusCommand(args)
		return

	case "dm", "direct":
		d.handleDirectMessageCommand(ctx, args)
		return

	case "group":
		d.handleGroupCommand(ctx, args)
		return

	case "groups":
		d.showGroups()
		return

	case "template", "t":
		d.handleTemplateCommand(ctx, args)
		return

	case "templates":
		d.showTemplates()
		return
	}

	// If we have focused agents, only send to them
	if len(d.FocusedAgents) > 0 {
		fmt.Fprintf(d.OutputWriter, "[green]> %s [cyan](focused agents only)[white]\n", cmdStr)
		go d.Orchestrator.ProcessCommandForAgents(ctx, cmdStr, d.getFocusedAgentsList())
	} else {
		// Otherwise send to all agents
		fmt.Fprintf(d.OutputWriter, "[green]> %s[white]\n", cmdStr)
		go d.Orchestrator.ProcessCommand(ctx, cmdStr)
	}
}

// showHelp displays help information
func (d *Dashboard) showHelp() {
	help := `
[yellow]Available Commands:[white]
[green]health[white] - Check the health of all agents
[green]focus <agent1> <agent2> ...[white] - Focus on specific agents
[green]unfocus <agent1> <agent2> ...[white] - Remove focus from agents (or 'all' to clear focus)
[green]dm <agent> <message>[white] - Send a direct message to a specific agent
[green]group <groupname> <message>[white] - Send a message to a group of agents
[green]groups[white] - List available agent groups
[green]template <name> [args][white] - Use a command template
[green]templates[white] - List available templates
[green]help[white] - Show this help information
[green]quit[white] or [green]exit[white] - Exit the application

For regular commands, if agents are focused, commands only go to focused agents.
`
	fmt.Fprintf(d.OutputWriter, "%s", help)
}

// handleFocusCommand processes the focus command
func (d *Dashboard) handleFocusCommand(args []string) {
	if len(args) == 0 {
		fmt.Fprintf(d.OutputWriter, "[yellow]Usage: focus <agent1> <agent2> ...[white]\n")
		return
	}

	// Clear focus if "all" is specified
	if len(args) == 1 && args[0] == "all" {
		d.FocusedAgents = make(map[string]bool)
		fmt.Fprintf(d.OutputWriter, "[yellow]Focus cleared - commands will go to all agents.[white]\n")

		// Reset all panel colors
		for _, agent := range d.Config.Agents {
			panel := d.AgentPanels[agent.Name]
			if panel != nil {
				panel.SetBorderColor(tcell.ColorBlue)
			}
		}
		return
	}

	// Focus on specified agents
	newFocus := false
	for _, agentName := range args {
		// Check if agent exists
		found := false
		for _, agent := range d.Config.Agents {
			if strings.EqualFold(agent.Name, agentName) {
				d.FocusedAgents[agent.Name] = true
				panel := d.AgentPanels[agent.Name]
				if panel != nil {
					panel.SetBorderColor(tcell.ColorGreen)
				}
				found = true
				newFocus = true
				break
			}
		}

		if !found {
			fmt.Fprintf(d.OutputWriter, "[red]Agent not found: %s[white]\n", agentName)
		}
	}

	if newFocus {
		fmt.Fprintf(d.OutputWriter, "[yellow]Focus set - commands will only go to focused agents.[white]\n")
	}
}

// handleUnfocusCommand processes the unfocus command
func (d *Dashboard) handleUnfocusCommand(args []string) {
	if len(args) == 0 {
		fmt.Fprintf(d.OutputWriter, "[yellow]Usage: unfocus <agent1> <agent2> ... or 'all' to clear focus[white]\n")
		return
	}

	// Clear all focus if "all" is specified
	if len(args) == 1 && args[0] == "all" {
		d.FocusedAgents = make(map[string]bool)
		fmt.Fprintf(d.OutputWriter, "[yellow]Focus cleared - commands will go to all agents.[white]\n")

		// Reset all panel colors
		for _, agent := range d.Config.Agents {
			panel := d.AgentPanels[agent.Name]
			if panel != nil {
				panel.SetBorderColor(tcell.ColorBlue)
			}
		}
		return
	}

	// Unfocus specified agents
	for _, agentName := range args {
		// Check if agent exists
		for _, agent := range d.Config.Agents {
			if strings.EqualFold(agent.Name, agentName) {
				delete(d.FocusedAgents, agent.Name)
				panel := d.AgentPanels[agent.Name]
				if panel != nil {
					panel.SetBorderColor(tcell.ColorBlue)
				}
				break
			}
		}
	}

	// If no more focused agents, notify
	if len(d.FocusedAgents) == 0 {
		fmt.Fprintf(d.OutputWriter, "[yellow]Focus cleared - commands will go to all agents.[white]\n")
	} else {
		fmt.Fprintf(d.OutputWriter, "[yellow]Agents unfocused - %d agents still in focus.[white]\n", len(d.FocusedAgents))
	}
}

// handleDirectMessageCommand processes a direct message command
func (d *Dashboard) handleDirectMessageCommand(ctx context.Context, args []string) {
	if len(args) < 2 {
		fmt.Fprintf(d.OutputWriter, "[yellow]Usage: dm <agent> <message>[white]\n")
		return
	}

	agentName := args[0]
	message := strings.Join(args[1:], " ")

	// Find target agent
	found := false
	var targetAgent Agent
	for _, agent := range d.Config.Agents {
		if strings.EqualFold(agent.Name, agentName) {
			targetAgent = agent
			found = true
			break
		}
	}

	if !found {
		fmt.Fprintf(d.OutputWriter, "[red]Agent not found: %s[white]\n")
		return
	}

	// Send direct message
	fmt.Fprintf(d.OutputWriter, "[green]> Direct message to %s: %s[white]\n", targetAgent.Name, message)
	go d.Orchestrator.ProcessDirectMessage(ctx, message, targetAgent)
}

// handleGroupCommand processes a group command
func (d *Dashboard) handleGroupCommand(ctx context.Context, args []string) {
	if len(args) < 2 {
		fmt.Fprintf(d.OutputWriter, "[yellow]Usage: group <groupname> <message>[white]\n")
		return
	}

	groupName := args[0]
	message := strings.Join(args[1:], " ")

	// Find group
	members, exists := d.Config.Groups[groupName]
	if !exists {
		fmt.Fprintf(d.OutputWriter, "[red]Group not found: %s[white]\n", groupName)
		fmt.Fprintf(d.OutputWriter, "[yellow]Available groups: %s[white]\n", strings.Join(getGroupNames(d.Config.Groups), ", "))
		return
	}

	// Get agents for this group
	var groupAgents []Agent
	for _, member := range members {
		for _, agent := range d.Config.Agents {
			if agent.Name == member {
				groupAgents = append(groupAgents, agent)
				break
			}
		}
	}

	if len(groupAgents) == 0 {
		fmt.Fprintf(d.OutputWriter, "[red]No agents found in group: %s[white]\n", groupName)
		return
	}

	// Send message to group
	fmt.Fprintf(d.OutputWriter, "[green]> Group message to '%s' (%d agents): %s[white]\n",
		groupName, len(groupAgents), message)
	go d.Orchestrator.ProcessCommandForAgents(ctx, message, groupAgents)
}

// showGroups displays available agent groups
func (d *Dashboard) showGroups() {
	if len(d.Config.Groups) == 0 {
		fmt.Fprintf(d.OutputWriter, "[yellow]No agent groups defined.[white]\n")
		return
	}

	fmt.Fprintf(d.OutputWriter, "[yellow]Available Agent Groups:[white]\n")
	for name, members := range d.Config.Groups {
		fmt.Fprintf(d.OutputWriter, "[green]%s[white] (%d members): %s\n",
			name, len(members), strings.Join(members, ", "))
	}
}

// handleTemplateCommand processes a template command
func (d *Dashboard) handleTemplateCommand(ctx context.Context, args []string) {
	if len(args) < 1 {
		fmt.Fprintf(d.OutputWriter, "[yellow]Usage: template <name> [args][white]\n")
		return
	}

	templateName := args[0]
	templateText, exists := d.Config.Templates[templateName]
	if !exists {
		fmt.Fprintf(d.OutputWriter, "[red]Template not found: %s[white]\n", templateName)
		fmt.Fprintf(d.OutputWriter, "[yellow]Available templates: %s[white]\n",
			strings.Join(getTemplateNames(d.Config.Templates), ", "))
		return
	}

	// Process template with placeholders
	command := templateText
	if len(args) > 1 {
		placeholderArgs := strings.Join(args[1:], " ")
		command = strings.Replace(command, "[TOPIC]", placeholderArgs, -1)
		command = strings.Replace(command, "[SITUATION]", placeholderArgs, -1)
	}

	// Process the command
	fmt.Fprintf(d.OutputWriter, "[green]> Template '%s': %s[white]\n", templateName, command)

	// If we have focused agents, only send to them
	if len(d.FocusedAgents) > 0 {
		go d.Orchestrator.ProcessCommandForAgents(ctx, command, d.getFocusedAgentsList())
	} else {
		// Otherwise send to all agents
		go d.Orchestrator.ProcessCommand(ctx, command)
	}
}

// showTemplates displays available command templates
func (d *Dashboard) showTemplates() {
	if len(d.Config.Templates) == 0 {
		fmt.Fprintf(d.OutputWriter, "[yellow]No command templates defined.[white]\n")
		return
	}

	fmt.Fprintf(d.OutputWriter, "[yellow]Available Command Templates:[white]\n")
	for name, template := range d.Config.Templates {
		fmt.Fprintf(d.OutputWriter, "[green]%s[white]: %s\n", name, template)
	}
}

// getFocusedAgentsList returns a list of agents that are currently focused
func (d *Dashboard) getFocusedAgentsList() []Agent {
	var agents []Agent
	for _, agent := range d.Config.Agents {
		if d.FocusedAgents[agent.Name] {
			agents = append(agents, agent)
		}
	}
	return agents
}

// getGroupNames returns a list of group names
func getGroupNames(groups map[string][]string) []string {
	names := make([]string, 0, len(groups))
	for name := range groups {
		names = append(names, name)
	}
	return names
}

// getTemplateNames returns a list of template names
func getTemplateNames(templates map[string]string) []string {
	names := make([]string, 0, len(templates))
	for name := range templates {
		names = append(names, name)
	}
	return names
}

func main() {
	// Initialize random seed
	rand.Seed(time.Now().UnixNano())

	flag.Parse()

	// Create default config if doesn't exist
	if err := CreateDefaultConfig(*configPath); err != nil {
		log.Printf("Warning: Failed to create default config: %v", err)
	}

	// Ensure log directory exists
	if err := EnsureLogDirectory(*logPath); err != nil {
		log.Fatalf("Failed to create log directory: %v", err)
	}

	// Load agent configuration
	config, err := loadAgentConfig(*configPath)
	if err != nil {
		log.Fatalf("Failed to load agent configuration: %v", err)
	}

	// Initialize logger
	logger, err := NewLogger(*logPath, *jsonLogs)
	if err != nil {
		log.Fatalf("Failed to initialize logger: %v", err)
	}
	defer logger.Close()

	// Initialize API client
	apiClient := NewAPIClient(*timeoutSec)

	// Create dashboard
	dashboard := NewDashboard(config)

	// Create application UI
	app := tview.NewApplication()
	dashboard.App = app

	// Create a grid layout
	grid := tview.NewGrid()

	// Calculate grid dimensions based on agent count
	agentCount := len(config.Agents)
	rows := (agentCount + 2) / 3 // 3 columns, calculate rows needed

	// Configure the grid with flexible columns and rows
	grid.SetRows(make([]int, rows)...).
		SetColumns(0, 0, 0).
		SetBorders(true)

	// Create terminal panels for each agent
	for i, agent := range config.Agents {
		// Create TextView
		panel := tview.NewTextView()
		panel.SetDynamicColors(true)
		panel.SetScrollable(true)
		panel.SetTitle(fmt.Sprintf(" %s (%s) ", agent.Name, agent.Role))
		panel.SetTitleColor(tcell.ColorYellow)
		panel.SetBorder(true)
		panel.SetBorderColor(tcell.ColorBlue)
		panel.SetText(fmt.Sprintf("[yellow]Agent: %s\nRole: %s\nURL: %s\nModel: %s[white]\n\nWaiting for activity...",
			agent.Name, agent.Role, agent.URL, agent.Model))

		row := i / 3
		col := i % 3

		grid.AddItem(panel, row, col, 1, 1, 0, 0, false)
		dashboard.AgentPanels[agent.Name] = panel
	}

	// Create a main terminal for user interaction
	commandInput := tview.NewInputField().
		SetLabel("Command: ").
		SetFieldWidth(0).
		SetFieldBackgroundColor(tcell.ColorBlack)

	// Add command history navigation
	commandInput.SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
		switch event.Key() {
		case tcell.KeyUp:
			// Navigate up through history
			if dashboard.HistoryPos > 0 {
				dashboard.HistoryPos--
				commandInput.SetText(dashboard.CommandHistory[dashboard.HistoryPos])
			}
			return nil
		case tcell.KeyDown:
			// Navigate down through history
			if dashboard.HistoryPos < len(dashboard.CommandHistory)-1 {
				dashboard.HistoryPos++
				commandInput.SetText(dashboard.CommandHistory[dashboard.HistoryPos])
			} else if dashboard.HistoryPos == len(dashboard.CommandHistory)-1 {
				// At the end of history, clear the input
				dashboard.HistoryPos = len(dashboard.CommandHistory)
				commandInput.SetText("")
			}
			return nil
		}
		return event
	})

	// Create output view for main terminal
	outputView := tview.NewTextView()
	outputView.SetDynamicColors(true)
	outputView.SetScrollable(true)
	outputView.SetTitle(" Main Console ")
	outputView.SetTitleColor(tcell.ColorYellow)
	outputView.SetBorder(true)

	// Create a writer for the output view
	outputWriter := &Writer{TextView: outputView}
	dashboard.OutputView = outputView
	dashboard.OutputWriter = outputWriter

	// Add the main terminal to the grid
	mainTerminalFlex := tview.NewFlex().SetDirection(tview.FlexRow).
		AddItem(outputView, 0, 4, false).
		AddItem(commandInput, 1, 1, true)

	// Add main terminal to the bottom of the grid
	grid.AddItem(mainTerminalFlex, rows, 0, 1, 3, 0, 0, true)

	// Create orchestrator
	orchestrator := NewOrchestrator(
		config.Agents,
		apiClient,
		logger,
		dashboard.AgentPanels,
		app,
		outputView,
	)
	dashboard.Orchestrator = orchestrator

	// Set up context for clean shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Set up command handling
	commandInput.SetDoneFunc(func(key tcell.Key) {
		if key == tcell.KeyEnter {
			command := commandInput.GetText()
			if command == "" {
				return
			}

			// Process the command
			dashboard.ProcessCommand(ctx, command)

			// Clear the input field
			commandInput.SetText("")
		}
	})

	// Start monitoring agent logs
	go monitorAgentLogs(ctx, config.Agents, dashboard.AgentPanels, app)

	// Set input capture to handle global keys
	app.SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
		if event.Key() == tcell.KeyCtrlC {
			app.Stop()
			return nil
		}
		return event
	})

	// Handle system signals for clean shutdown
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigs
		app.Stop()
	}()

	// Initial welcome message
	fmt.Fprintf(outputWriter, "[yellow]Welcome to Celaya Multi-Agent Dashboard![white]\n")
	fmt.Fprintf(outputWriter, "[cyan]Type a command to send to all agents or 'help' for available commands.[white]\n")
	fmt.Fprintf(outputWriter, "[cyan]Press Ctrl+C to exit.[white]\n")

	// Run health check on startup
	go func() {
		// Wait a moment for UI to initialize
		time.Sleep(time.Second)
		fmt.Fprintf(outputWriter, "[yellow]Checking agent health...[white]\n")
		orchestrator.CheckAgentHealth(ctx)
	}()

	// Set root and start the application
	if err := app.SetRoot(grid, true).EnableMouse(true).Run(); err != nil {
		log.Fatalf("Error running application: %v", err)
	}
}

// monitorAgentLogs monitors log files for all agents and updates their panels
func monitorAgentLogs(ctx context.Context, agents []Agent, panels map[string]*tview.TextView, app *tview.Application) {
	var wg sync.WaitGroup

	for _, agent := range agents {
		wg.Add(1)
		go func(a Agent) {
			defer wg.Done()

			logFile := fmt.Sprintf("%s/agent_%s.log", *logPath, a.Name)

			// Create log file if it doesn't exist
			if _, err := os.Stat(logFile); os.IsNotExist(err) {
				file, err := os.Create(logFile)
				if err != nil {
					log.Printf("Error creating log file for agent %s: %v", a.Name, err)
					return
				}
				file.Close()
			}

			// Use tail to monitor the log file
			cmd := exec.Command("tail", "-f", logFile)
			stdout, err := cmd.StdoutPipe()
			if err != nil {
				log.Printf("Error setting up log monitoring for agent %s: %v", a.Name, err)
				return
			}

			if err := cmd.Start(); err != nil {
				log.Printf("Error starting log monitoring for agent %s: %v", a.Name, err)
				return
			}

			// Create a scanner to read from the stdout pipe
			scanner := bufio.NewScanner(stdout)

			// Monitor for new lines in the log file
			go func() {
				for scanner.Scan() {
					line := scanner.Text()

					// Parse the log entry if possible
					entry := parseLogEntry(line, a.Name)

					// Update the agent panel with the new log entry
					app.QueueUpdateDraw(func() {
						panel := panels[a.Name]
						if panel != nil {
							// Format the log entry based on type
							var formattedEntry string
							if entry.Action != "" {
								formattedEntry = fmt.Sprintf("[yellow]%s [ACTION][white] %s\n",
									entry.Timestamp.Format("15:04:05"), entry.Action)
							} else if entry.Response != "" {
								formattedEntry = fmt.Sprintf("[green]%s [RESPONSE][white] %s\n",
									entry.Timestamp.Format("15:04:05"), entry.Response)
							} else {
								formattedEntry = fmt.Sprintf("[blue]%s [%s][white] %s\n",
									entry.Timestamp.Format("15:04:05"), entry.Level, entry.Message)
							}

							// Append the log entry to the panel
							fmt.Fprint(panel, formattedEntry)

							// Auto-scroll to the bottom
							panel.ScrollToEnd()
						}
					})
				}
			}()

			// Wait for context cancellation to clean up
			<-ctx.Done()
			cmd.Process.Kill()
			cmd.Wait()

		}(agent)
	}

	// Wait for all monitoring goroutines to complete
	wg.Wait()
}

// parseLogEntry parses a log entry from a string
func parseLogEntry(line string, agentName string) LogEntry {
	entry := LogEntry{
		Timestamp: time.Now(),
		Level:     "INFO",
		Message:   line,
		Agent:     agentName,
	}

	// Try to parse JSON if the line looks like JSON
	if len(line) > 0 && line[0] == '{' {
		err := json.Unmarshal([]byte(line), &entry)
		if err != nil {
			// If parsing fails, just use the line as the message
			entry.Message = line
		}
	}

	return entry
}
