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
}

// AgentConfig represents the configuration for all agents
type AgentConfig struct {
	Agents   []Agent                `json:"agents"`
	Settings map[string]interface{} `json:"settings"`
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

	// Create application UI
	app := tview.NewApplication()

	// Create a grid layout
	grid := tview.NewGrid()

	// Create terminal panels for each agent
	agentPanels := make(map[string]*tview.TextView)

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
		agentPanels[agent.Name] = panel
	}

	// Create a main terminal for user interaction
	commandInput := tview.NewInputField().
		SetLabel("Command: ").
		SetFieldWidth(0).
		SetFieldBackgroundColor(tcell.ColorBlack)

	// Create output view for main terminal
	outputView := tview.NewTextView()
	outputView.SetDynamicColors(true)
	outputView.SetScrollable(true)
	outputView.SetTitle(" Main Console ")
	outputView.SetTitleColor(tcell.ColorYellow)
	outputView.SetBorder(true)

	// Create a writer for the output view
	outputWriter := &Writer{TextView: outputView}

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
		agentPanels,
		app,
		outputView,
	)

	// Set up context for clean shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Set up command handling
	commandInput.SetDoneFunc(func(key tcell.Key) {
		if key == tcell.KeyEnter {
			command := commandInput.GetText()

			if command == "quit" || command == "exit" {
				app.Stop()
				return
			}

			if command == "health" {
				// Check agent health
				fmt.Fprintf(outputWriter, "[yellow]Checking agent health...[white]\n")
				go orchestrator.CheckAgentHealth(ctx)
				commandInput.SetText("")
				return
			}

			// Display the command in the output view
			fmt.Fprintf(outputWriter, "[green]> %s[white]\n", command)

			// Process the command via orchestrator
			go orchestrator.ProcessCommand(ctx, command)

			// Clear the input field
			commandInput.SetText("")
		}
	})

	// Start monitoring agent logs
	go monitorAgentLogs(ctx, config.Agents, agentPanels, app)

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
	fmt.Fprintf(outputWriter, "[cyan]Type a command to send to all agents or 'health' to check agent health.[white]\n")
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
