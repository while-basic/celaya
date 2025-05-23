// ----------------------------------------------------------------------------
//  File:        log.go
//  Project:     Celaya Solutions (Agent Dashboard)
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: Logging utilities for the agent dashboard
//  Version:     1.0.0
//  License:     BSL (SPDX id BUSL)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// LogLevel represents a log level
type LogLevel string

const (
	INFO  LogLevel = "INFO"
	ERROR LogLevel = "ERROR"
	DEBUG LogLevel = "DEBUG"
	WARN  LogLevel = "WARN"
)

// Logger provides logging functionality
type Logger struct {
	baseDir  string
	jsonLogs bool
	files    map[string]*os.File
	mu       sync.Mutex
}

// NewLogger creates a new logger
func NewLogger(baseDir string, jsonLogs bool) (*Logger, error) {
	// Create logger
	logger := &Logger{
		baseDir:  baseDir,
		jsonLogs: jsonLogs,
		files:    make(map[string]*os.File),
	}

	return logger, nil
}

// Close closes all log files
func (l *Logger) Close() error {
	l.mu.Lock()
	defer l.mu.Unlock()

	var lastErr error
	for _, file := range l.files {
		if err := file.Close(); err != nil {
			lastErr = err
		}
	}

	return lastErr
}

// getLogFile gets or creates a log file for an agent
func (l *Logger) getLogFile(agentName string) (*os.File, error) {
	l.mu.Lock()
	defer l.mu.Unlock()

	// Check if file exists
	if file, ok := l.files[agentName]; ok {
		return file, nil
	}

	// Create log file
	fileName := fmt.Sprintf("agent_%s.log", agentName)
	filePath := filepath.Join(l.baseDir, fileName)

	file, err := os.OpenFile(filePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return nil, err
	}

	// Store file
	l.files[agentName] = file

	return file, nil
}

// LogInfo logs an info message for an agent
func (l *Logger) LogInfo(agentName, message string) error {
	return l.log(agentName, INFO, message, "", "")
}

// LogError logs an error message for an agent
func (l *Logger) LogError(agentName, message string) error {
	return l.log(agentName, ERROR, message, "", "")
}

// LogDebug logs a debug message for an agent
func (l *Logger) LogDebug(agentName, message string) error {
	return l.log(agentName, DEBUG, message, "", "")
}

// LogWarn logs a warning message for an agent
func (l *Logger) LogWarn(agentName, message string) error {
	return l.log(agentName, WARN, message, "", "")
}

// LogAction logs an action performed by an agent
func (l *Logger) LogAction(agentName, action string) error {
	return l.log(agentName, INFO, "", action, "")
}

// LogResponse logs a response from an agent
func (l *Logger) LogResponse(agentName, response string) error {
	return l.log(agentName, INFO, "", "", response)
}

// log logs a message to an agent's log file
func (l *Logger) log(agentName string, level LogLevel, message, action, response string) error {
	// Get log file
	file, err := l.getLogFile(agentName)
	if err != nil {
		return err
	}

	// Create log entry
	now := time.Now()

	if l.jsonLogs {
		// Create log entry as JSON
		entry := map[string]interface{}{
			"timestamp": now.Format(time.RFC3339),
			"level":     level,
			"agent":     agentName,
		}

		// Add message, action, or response
		if message != "" {
			entry["message"] = message
		}
		if action != "" {
			entry["action"] = action
		}
		if response != "" {
			entry["response"] = response
		}

		// Marshal to JSON
		data, err := json.Marshal(entry)
		if err != nil {
			return err
		}

		// Write to file
		if _, err := file.Write(data); err != nil {
			return err
		}
		if _, err := file.Write([]byte("\n")); err != nil {
			return err
		}
	} else {
		// Create log entry as plain text
		var logMessage string
		if message != "" {
			logMessage = fmt.Sprintf("[%s] [%s] %s: %s\n", now.Format(time.RFC3339), level, agentName, message)
		} else if action != "" {
			logMessage = fmt.Sprintf("[%s] [%s] %s: ACTION: %s\n", now.Format(time.RFC3339), level, agentName, action)
		} else if response != "" {
			logMessage = fmt.Sprintf("[%s] [%s] %s: RESPONSE: %s\n", now.Format(time.RFC3339), level, agentName, response)
		}

		// Write to file
		if _, err := file.WriteString(logMessage); err != nil {
			return err
		}
	}

	return nil
}
