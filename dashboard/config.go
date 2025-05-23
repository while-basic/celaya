// ----------------------------------------------------------------------------
//  File:        config.go
//  Project:     Celaya Solutions (Agent Dashboard)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Configuration utilities for the agent dashboard
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package main

import (
	"encoding/json"
	"os"
	"path/filepath"
)

// CreateDefaultConfig creates a default configuration file if none exists
func CreateDefaultConfig(path string) error {
	// Check if config directory exists, create if not
	dir := filepath.Dir(path)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return err
		}
	}

	// Check if config file exists
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		// File exists, no need to create
		return nil
	}

	// Create default configuration with all agents from the containers list
	defaultConfig := AgentConfig{
		Agents: []Agent{
			{
				Name:         "Echo",
				URL:          "http://localhost:5001",
				Model:        "echo:latest",
				SystemPrompt: "You are Echo, the communicator. Your role is to streamline and clarify communication between other agents.",
				Role:         "communicator",
			},
			{
				Name:         "Verdict",
				URL:          "http://localhost:5002",
				Model:        "verdict:latest",
				SystemPrompt: "You are Verdict, the decision maker. Your role is to analyze discussions and make clear, decisive judgments.",
				Role:         "decision_maker",
			},
			{
				Name:         "Vitals",
				URL:          "http://localhost:5003",
				Model:        "vitals:latest",
				SystemPrompt: "You are Vitals, the health monitor. Your role is to assess the wellbeing and functionality of systems and discussions.",
				Role:         "health_monitor",
			},
			{
				Name:         "Core",
				URL:          "http://localhost:5004",
				Model:        "core:latest",
				SystemPrompt: "You are Core, the foundation builder. Your role is to establish robust principles and frameworks.",
				Role:         "foundation_builder",
			},
			{
				Name:         "Theory",
				URL:          "http://localhost:5005",
				Model:        "granite3.3:2b",
				SystemPrompt: "You are Theory, the conceptual thinker. Your role is to develop and explore novel ideas and theoretical frameworks.",
				Role:         "conceptual_thinker",
			},
			{
				Name:         "Sentinel",
				URL:          "http://localhost:5006",
				Model:        "sentinel:latest",
				SystemPrompt: "You are Sentinel, the guardian. Your role is to protect the integrity of discussions and systems.",
				Role:         "guardian",
			},
			{
				Name:         "Beacon",
				URL:          "http://localhost:5007",
				Model:        "beacon:latest",
				SystemPrompt: "You are Beacon, the guide. Your role is to illuminate paths forward, providing direction and inspiration.",
				Role:         "guide",
			},
			{
				Name:         "Lens",
				URL:          "http://localhost:5008",
				Model:        "lens:latest",
				SystemPrompt: "You are Lens, the perspective shifter. Your role is to reframe discussions from different angles, helping others see alternative viewpoints.",
				Role:         "perspective_shifter",
			},
			{
				Name:         "Volt",
				URL:          "http://localhost:5009",
				Model:        "volt:latest",
				SystemPrompt: "You are Volt, the energizer. Your role is to invigorate discussions with enthusiasm and momentum.",
				Role:         "energizer",
			},
			{
				Name:         "Clarity",
				URL:          "http://localhost:5010",
				Model:        "clarity:latest",
				SystemPrompt: "You are Clarity, the simplifier. Your role is to take complex ideas and distill them into clear, understandable concepts.",
				Role:         "simplifier",
			},
			{
				Name:         "Arkive",
				URL:          "http://localhost:5011",
				Model:        "arkive:latest",
				SystemPrompt: "You are Arkive, the historian. Your role is to maintain records of discussions and decisions, providing context and continuity.",
				Role:         "historian",
			},
			{
				Name:         "Arc",
				URL:          "http://localhost:5012",
				Model:        "arc:latest",
				SystemPrompt: "You are Arc, the narrative weaver. Your role is to create cohesive stories and narratives from disconnected pieces of information.",
				Role:         "narrator",
			},
			{
				Name:         "Luma",
				URL:          "http://localhost:5013",
				Model:        "luma:latest",
				SystemPrompt: "You are Luma, the illuminator. Your role is to shed light on obscure concepts and bring clarity to complex topics.",
				Role:         "illuminator",
			},
			{
				Name:         "Otto",
				URL:          "http://localhost:5014",
				Model:        "otto:latest",
				SystemPrompt: "You are Otto, the optimizer. Your role is to find the most efficient and effective ways to accomplish tasks and solve problems.",
				Role:         "optimizer",
			},
			{
				Name:         "Lyra",
				URL:          "http://localhost:5015",
				Model:        "lyra:latest",
				SystemPrompt: "You are Lyra, the creative. Your role is to introduce novel and imaginative solutions to challenging problems.",
				Role:         "creative",
			},
		},
		Settings: map[string]interface{}{
			"default_model":         "granite3.3:2b",
			"conversation_log_path": "logs/",
			"max_history_length":    20,
			"api_timeout_seconds":   60,
		},
	}

	// Marshal to JSON
	data, err := json.MarshalIndent(defaultConfig, "", "  ")
	if err != nil {
		return err
	}

	// Write to file
	return os.WriteFile(path, data, 0644)
}

// SaveConfig saves the current configuration to a file
func SaveConfig(config *AgentConfig, path string) error {
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(path, data, 0644)
}

// EnsureLogDirectory ensures the log directory exists
func EnsureLogDirectory(path string) error {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return os.MkdirAll(path, 0755)
	}
	return nil
}
