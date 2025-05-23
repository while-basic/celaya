// ----------------------------------------------------------------------------
//  File:        api.go
//  Project:     Celaya Solutions (Agent Dashboard)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: API client for agent interactions
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"os"
	"strings"
	"time"
)

// APIClient is a client for agent API interactions
type APIClient struct {
	httpClient *http.Client
	simMode    bool
}

// GenerateRequest represents a request to generate text
type GenerateRequest struct {
	Model  string `json:"model"`
	Prompt string `json:"prompt"`
	System string `json:"system,omitempty"`
	Stream bool   `json:"stream,omitempty"`
}

// GenerateResponse represents a response from the generate API
type GenerateResponse struct {
	Response string `json:"response"`
	Model    string `json:"model"`
	Time     int64  `json:"time_ms"`
}

// NewAPIClient creates a new API client
func NewAPIClient(timeoutSec int) *APIClient {
	// Check if simulation mode is enabled
	simMode := os.Getenv("DASHBOARD_SIM_MODE") == "true"

	return &APIClient{
		httpClient: &http.Client{
			Timeout: time.Duration(timeoutSec) * time.Second,
		},
		simMode: simMode,
	}
}

// Generate calls the generate API
func (c *APIClient) Generate(ctx context.Context, url string, req *GenerateRequest) (*GenerateResponse, error) {
	// If in simulation mode, generate a simulated response
	if c.simMode {
		return c.simulateGenerate(req)
	}

	// Implementation for real API call would go here
	// For now, return an error
	return nil, fmt.Errorf("real API not implemented")
}

// SendCommand sends a command to an agent and returns the response
func (c *APIClient) SendCommand(ctx context.Context, agent Agent, command string) (string, error) {
	// If in simulation mode, generate a simulated response
	if c.simMode {
		return c.simulateCommand(agent, command)
	}

	// Create the generate request
	req := &GenerateRequest{
		Model:  agent.Model,
		Prompt: command,
		System: agent.SystemPrompt,
		Stream: false,
	}

	// Call the agent API
	res, err := c.Generate(ctx, agent.URL, req)
	if err != nil {
		return "", err
	}

	return res.Response, nil
}

// CheckHealth checks if an agent is healthy
func (c *APIClient) CheckHealth(ctx context.Context, agent Agent) (bool, error) {
	// If in simulation mode, simulate health check
	if c.simMode {
		return c.simulateHealthCheck(agent)
	}

	// Implementation for real API call would go here
	// For now, return an error
	return false, fmt.Errorf("real health check not implemented")
}

// Health checks if an agent is healthy
func (c *APIClient) Health(ctx context.Context, url string) (bool, error) {
	// If in simulation mode, simulate health check
	if c.simMode {
		return true, nil
	}

	// Create a request with context
	req, err := http.NewRequestWithContext(ctx, "GET", url+"/health", nil)
	if err != nil {
		return false, err
	}

	// Send the request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()

	// Check if the response is OK
	return resp.StatusCode == http.StatusOK, nil
}

// simulateGenerate simulates a response from an agent
func (c *APIClient) simulateGenerate(req *GenerateRequest) (*GenerateResponse, error) {
	// Parse some information from the request
	prompt := req.Prompt
	system := req.System

	// Add some delay to simulate network latency and processing time
	delay := rand.Intn(1000) + 500 // 500-1500ms
	time.Sleep(time.Duration(delay) * time.Millisecond)

	// Generate a response based on the prompt
	var response string
	if strings.Contains(strings.ToLower(prompt), "error") {
		return nil, fmt.Errorf("simulated error for prompt containing 'error'")
	} else if strings.Contains(system, "research") {
		response = fmt.Sprintf("Research analysis: The topic '%s' has multiple facets we should explore...", prompt)
	} else if strings.Contains(system, "creative") {
		response = fmt.Sprintf("Creative idea: Based on '%s', we could create something that combines...", prompt)
	} else if strings.Contains(system, "critic") {
		response = fmt.Sprintf("Critical assessment: There are several issues with '%s' that need to be addressed...", prompt)
	} else if strings.Contains(strings.ToLower(prompt), "hello") || strings.Contains(strings.ToLower(prompt), "hi") {
		response = "Hello! How can I assist you today?"
	} else if strings.Contains(strings.ToLower(prompt), "time") {
		response = fmt.Sprintf("The current time is %s", time.Now().Format("15:04:05"))
	} else if strings.Contains(strings.ToLower(prompt), "help") {
		response = "I'm here to help! You can ask me about various topics, and I'll do my best to provide information or assistance."
	} else if strings.Contains(strings.ToLower(prompt), "summarize") || strings.Contains(strings.ToLower(prompt), "summary") {
		response = "Here's a summary of the key points: 1) First important point... 2) Second important consideration... 3) Finally..."
	} else if strings.Contains(strings.ToLower(prompt), "analyze") || strings.Contains(strings.ToLower(prompt), "analysis") {
		response = "Based on my analysis: The primary factors to consider are A, B, and C. The implications suggest that..."
	} else if strings.Contains(strings.ToLower(prompt), "plan") || strings.Contains(strings.ToLower(prompt), "steps") {
		response = "Here's a step-by-step plan: 1. First, we should... 2. Next, it's important to... 3. Finally, we'll need to..."
	} else {
		// Generic response
		promptWords := strings.Fields(prompt)
		responseLength := rand.Intn(3) + 2 // 2-4 sentences

		response = "I've processed your request"
		if len(promptWords) > 0 {
			response += fmt.Sprintf(" about '%s'", promptWords[rand.Intn(len(promptWords))])
		}
		response += ". "

		for i := 0; i < responseLength; i++ {
			response += "This is an important consideration. "
		}
	}

	return &GenerateResponse{
		Response: response,
		Model:    req.Model,
		Time:     int64(delay),
	}, nil
}

// simulateCommand simulates a response to a command
func (c *APIClient) simulateCommand(agent Agent, command string) (string, error) {
	// Add some delay to simulate network latency and processing time
	delay := rand.Intn(1000) + 500 // 500-1500ms
	time.Sleep(time.Duration(delay) * time.Millisecond)

	// Generate a response based on the agent's role and the command
	var response string

	// Check for error trigger
	if strings.Contains(strings.ToLower(command), "error") {
		return "", fmt.Errorf("simulated error for command containing 'error'")
	}

	// Role-specific responses
	switch strings.ToLower(agent.Role) {
	case "researcher", "research":
		response = fmt.Sprintf("As a researcher, I've looked into '%s'. The data suggests that...", command)
	case "analyst", "analysis":
		response = fmt.Sprintf("Analysis: '%s' has several important implications: 1) First point... 2) Second point...", command)
	case "creative", "creator":
		response = fmt.Sprintf("Creative perspective: '%s' inspires me to think about... Let me share some ideas...", command)
	case "critic", "critical":
		response = fmt.Sprintf("Critical assessment of '%s': There are several aspects to consider critically...", command)
	case "expert", "specialist":
		response = fmt.Sprintf("Expert opinion on '%s': Based on my specialized knowledge, I can tell you that...", command)
	default:
		// Generic response based on command content
		if strings.Contains(strings.ToLower(command), "hello") || strings.Contains(strings.ToLower(command), "hi") {
			response = fmt.Sprintf("Hello! I'm %s, and I'm here to help with %s.", agent.Name, agent.Role)
		} else if strings.Contains(strings.ToLower(command), "introduce") {
			response = fmt.Sprintf("I'm %s, focused on %s. My purpose is to provide insights and assistance in this area.",
				agent.Name, agent.Role)
		} else if strings.Contains(strings.ToLower(command), "summarize") || strings.Contains(strings.ToLower(command), "summary") {
			response = "Here's a summary: The key aspects to consider are A, B, and C. Each has different implications."
		} else if strings.Contains(strings.ToLower(command), "analyze") || strings.Contains(strings.ToLower(command), "analysis") {
			response = fmt.Sprintf("Analysis of '%s': There are multiple factors at play here. First...", command)
		} else if strings.Contains(strings.ToLower(command), "plan") {
			response = "Here's a plan: 1) First we should... 2) Then we need to... 3) Finally, we'll..."
		} else {
			// Very generic fallback
			response = fmt.Sprintf("I've considered '%s' and have the following thoughts: This is an important topic that requires careful consideration...", command)
		}
	}

	return response, nil
}

// simulateHealthCheck simulates a health check for an agent
func (c *APIClient) simulateHealthCheck(agent Agent) (bool, error) {
	// Add some delay to simulate network latency
	delay := rand.Intn(300) + 100 // 100-400ms
	time.Sleep(time.Duration(delay) * time.Millisecond)

	// Randomly determine if the agent is healthy (90% chance of being healthy)
	isHealthy := rand.Float32() < 0.9

	// If unhealthy, sometimes return an error instead of false
	if !isHealthy && rand.Float32() < 0.5 {
		return false, fmt.Errorf("simulated connection error to %s", agent.URL)
	}

	return isHealthy, nil
}

// StartOrchestratorTask sends a task to the orchestrator to be processed by all agents
func (c *APIClient) StartOrchestratorTask(ctx context.Context, orchestratorURL string, task string) (string, error) {
	// If in simulate mode, return simulated task ID
	if c.simMode {
		return fmt.Sprintf("sim-task-%d", rand.Intn(10000)), nil
	}

	// Create request body
	reqBody := map[string]string{
		"prompt": task,
	}

	// Marshal request to JSON
	data, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("error marshaling request: %w", err)
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(ctx, "POST", fmt.Sprintf("%s/api/orchestrate", orchestratorURL), bytes.NewBuffer(data))
	if err != nil {
		return "", fmt.Errorf("error creating request: %w", err)
	}

	// Set headers
	httpReq.Header.Set("Content-Type", "application/json")

	// Send request
	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return "", fmt.Errorf("error sending request: %w", err)
	}
	defer resp.Body.Close()

	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("error reading response: %w", err)
	}

	// Check response status
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("error response from orchestrator: %d - %s", resp.StatusCode, string(body))
	}

	// Parse response
	var response struct {
		TaskID string `json:"task_id"`
	}
	if err := json.Unmarshal(body, &response); err != nil {
		return "", fmt.Errorf("error unmarshaling response: %w", err)
	}

	return response.TaskID, nil
}
