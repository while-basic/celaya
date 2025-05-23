// ----------------------------------------------------------------------------
//  File:        api.go
//  Project:     Celaya Solutions (Agent Dashboard)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: API client for communicating with Celaya agents
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
	"strings"
	"time"
)

// APIClient provides methods for communicating with Celaya agent APIs
type APIClient struct {
	client       *http.Client
	timeout      time.Duration
	simulateMode bool
}

// GenerateRequest represents a request to the Celaya generate API
type GenerateRequest struct {
	Model   string        `json:"model"`
	Prompt  string        `json:"prompt"`
	System  string        `json:"system,omitempty"`
	Stream  bool          `json:"stream"`
	Context []interface{} `json:"context,omitempty"`
}

// GenerateResponse represents a response from the Celaya generate API
type GenerateResponse struct {
	Response string `json:"response"`
	Done     bool   `json:"done"`
}

// NewAPIClient creates a new API client with the specified timeout
func NewAPIClient(timeoutSeconds int) *APIClient {
	return &APIClient{
		client: &http.Client{
			Timeout: time.Duration(timeoutSeconds) * time.Second,
		},
		timeout:      time.Duration(timeoutSeconds) * time.Second,
		simulateMode: true, // Set to true to simulate responses instead of calling real APIs
	}
}

// Generate sends a generate request to the specified agent URL
func (c *APIClient) Generate(ctx context.Context, agentURL string, req *GenerateRequest) (*GenerateResponse, error) {
	// If in simulate mode, return simulated response
	if c.simulateMode {
		return c.simulateResponse(req)
	}

	// Marshal request to JSON
	data, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("error marshaling request: %w", err)
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(ctx, "POST", fmt.Sprintf("%s/api/generate", agentURL), bytes.NewBuffer(data))
	if err != nil {
		return nil, fmt.Errorf("error creating request: %w", err)
	}

	// Set headers
	httpReq.Header.Set("Content-Type", "application/json")

	// Send request
	resp, err := c.client.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("error sending request: %w", err)
	}
	defer resp.Body.Close()

	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %w", err)
	}

	// Check response status
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("error response from API: %d - %s", resp.StatusCode, string(body))
	}

	// Unmarshal response
	var response GenerateResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("error unmarshaling response: %w", err)
	}

	return &response, nil
}

// simulateResponse creates a simulated response based on the agent role
func (c *APIClient) simulateResponse(req *GenerateRequest) (*GenerateResponse, error) {
	// Simulate processing time
	simulateThinking := time.Duration(500 + rand.Intn(2000))
	time.Sleep(simulateThinking * time.Millisecond)

	// Extract agent name and role from the prompt
	agentName, role := extractAgentInfo(req.Prompt)

	// Get appropriate response based on role
	response := generateRoleBasedResponse(role, req.Prompt, agentName)

	return &GenerateResponse{
		Response: response,
		Done:     true,
	}, nil
}

// extractAgentInfo extracts agent name and role from the prompt
func extractAgentInfo(prompt string) (string, string) {
	// Default values
	agentName := "Unknown"
	role := "assistant"

	// Try to extract agent name and role from the prompt
	// Format is typically "Respond as {name} ({role})."
	if strings.Contains(prompt, "Respond as") {
		parts := strings.Split(prompt, "Respond as ")
		if len(parts) > 1 {
			infoStr := parts[1]
			// Extract agent name
			if strings.Contains(infoStr, "(") {
				namePart := strings.Split(infoStr, "(")[0]
				agentName = strings.TrimSpace(namePart)

				// Extract role
				rolePart := strings.Split(infoStr, "(")[1]
				if strings.Contains(rolePart, ")") {
					role = strings.Split(rolePart, ")")[0]
				}
			}
		}
	}

	return agentName, role
}

// generateRoleBasedResponse generates a response based on the agent's role
func generateRoleBasedResponse(role, prompt, agentName string) string {
	// Extract the actual command from the prompt
	command := extractCommand(prompt)

	// Different response templates based on role
	responses := map[string][]string{
		"communicator": {
			"I've received your command about %s and will relay it to others.",
			"Your request about %s has been clearly communicated to the team.",
			"Message about %s received and understood. Proceeding with coordination.",
		},
		"decision_maker": {
			"After analyzing %s, I recommend proceeding with this approach.",
			"Based on available data about %s, this is the optimal course of action.",
			"I've evaluated the options regarding %s and made a decision on how to proceed.",
		},
		"health_monitor": {
			"System health is stable after processing the request about %s.",
			"All vital signs are normal during this operation related to %s.",
			"Processing this request about %s has no negative impact on system health.",
		},
		"foundation_builder": {
			"This request about %s aligns with our core architectural principles.",
			"I'm establishing a framework to handle %s efficiently.",
			"Building a solid foundation for implementing this feature related to %s.",
		},
		"conceptual_thinker": {
			"This topic of %s opens interesting theoretical possibilities we should explore.",
			"I'm developing a conceptual model for %s.",
			"There are novel approaches we could take with %s.",
		},
		"guardian": {
			"Verified security implications of %s. Proceeding safely.",
			"Monitoring for potential vulnerabilities during this operation related to %s.",
			"Security checks for %s passed. This operation is authorized.",
		},
		"guide": {
			"I'll help navigate the implementation of %s.",
			"Let me illuminate the path forward for %s.",
			"I'm providing direction on how best to approach %s.",
		},
		"perspective_shifter": {
			"Have we considered alternative approaches to %s?",
			"Looking at %s from another angle reveals new possibilities.",
			"Reframing %s helps us see better solutions.",
		},
		"energizer": {
			"Let's move forward with enthusiasm and momentum on %s!",
			"I'm excited about the potential of %s!",
			"This direction with %s is great! Let's make it happen!",
		},
		"simplifier": {
			"To put it simply, for %s we need to focus on the core functionality.",
			"Let me break %s down into manageable steps.",
			"The essence of %s is straightforward.",
		},
		"historian": {
			"We've encountered similar situations to %s in the past with good results.",
			"This approach to %s aligns with our previous successful strategies.",
			"I'm logging this decision about %s for future reference.",
		},
		"narrator": {
			"Let me weave %s into our ongoing narrative.",
			"This %s chapter connects well with our previous storylines.",
			"I can craft a compelling story around %s for better understanding.",
		},
		"illuminator": {
			"Let me shed light on the complexities of %s.",
			"The subtle nuances of %s become clear when we examine them carefully.",
			"I can illuminate the hidden aspects of %s for everyone.",
		},
		"optimizer": {
			"I've found several ways to optimize the approach to %s.",
			"We can streamline our handling of %s by focusing on efficiency.",
			"The most effective way to deal with %s is to optimize our workflow.",
		},
		"creative": {
			"What if we approached %s in a completely novel way?",
			"I have an imaginative solution for %s that breaks conventional patterns.",
			"Let's think outside the box for %s and create something extraordinary.",
		},
	}

	// Default to basic responses if role not found
	roleResponses, ok := responses[role]
	if !ok {
		roleResponses = []string{
			"I've processed your request about %s and have a response.",
			"Regarding %s, I have some thoughts to share.",
			"I've analyzed %s and have prepared a response.",
		}
	}

	// Select a random response for variety
	index := rand.Intn(len(roleResponses))
	template := roleResponses[index]

	// Format the response with the command summary
	return fmt.Sprintf(template, command)
}

// extractCommand gets the actual command from the prompt
func extractCommand(prompt string) string {
	if strings.Contains(prompt, "Command from user:") {
		parts := strings.Split(prompt, "Command from user:")
		if len(parts) > 1 {
			commandPart := strings.Split(parts[1], "\n")[0]
			return strings.TrimSpace(commandPart)
		}
	}
	return "this request"
}

// Health checks if an agent is healthy by pinging its health endpoint
func (c *APIClient) Health(ctx context.Context, agentURL string) (bool, error) {
	// If in simulate mode, return simulated health status
	if c.simulateMode {
		// Simulate some failures randomly
		return rand.Float32() > 0.1, nil
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(ctx, "GET", fmt.Sprintf("%s/api/health", agentURL), nil)
	if err != nil {
		return false, fmt.Errorf("error creating request: %w", err)
	}

	// Send request
	resp, err := c.client.Do(httpReq)
	if err != nil {
		return false, fmt.Errorf("error sending request: %w", err)
	}
	defer resp.Body.Close()

	// Check response status
	return resp.StatusCode == http.StatusOK, nil
}

// StartOrchestratorTask sends a task to the orchestrator to be processed by all agents
func (c *APIClient) StartOrchestratorTask(ctx context.Context, orchestratorURL string, task string) (string, error) {
	// If in simulate mode, return simulated task ID
	if c.simulateMode {
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
	resp, err := c.client.Do(httpReq)
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
