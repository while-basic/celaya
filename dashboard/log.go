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

// Logger handles logging of agent activity
type Logger struct {
	logDir     string
	logFiles   map[string]*os.File
	mutex      sync.Mutex
	formatJSON bool
}

// NewLogger creates a new logger instance
func NewLogger(logDir string, formatJSON bool) (*Logger, error) {
	// Ensure log directory exists
	if err := os.MkdirAll(logDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create log directory: %w", err)
	}

	return &Logger{
		logDir:     logDir,
		logFiles:   make(map[string]*os.File),
		formatJSON: formatJSON,
	}, nil
}

// LogAgentAction logs an agent action
func (l *Logger) LogAgentAction(agentName, action string) error {
	l.mutex.Lock()
	defer l.mutex.Unlock()

	// Get log file for agent
	logFile, err := l.getLogFile(agentName)
	if err != nil {
		return err
	}

	// Create log entry
	timestamp := time.Now()
	entry := LogEntry{
		Timestamp: timestamp,
		Level:     "INFO",
		Message:   fmt.Sprintf("Agent %s performed action: %s", agentName, action),
		Agent:     agentName,
		Action:    action,
	}

	// Write log entry
	return l.writeLogEntry(logFile, entry)
}

// LogAgentResponse logs an agent response
func (l *Logger) LogAgentResponse(agentName, response string) error {
	l.mutex.Lock()
	defer l.mutex.Unlock()

	// Get log file for agent
	logFile, err := l.getLogFile(agentName)
	if err != nil {
		return err
	}

	// Create log entry
	timestamp := time.Now()
	entry := LogEntry{
		Timestamp: timestamp,
		Level:     "INFO",
		Message:   fmt.Sprintf("Agent %s responded: %s", agentName, response),
		Agent:     agentName,
		Response:  response,
	}

	// Write log entry
	return l.writeLogEntry(logFile, entry)
}

// LogAgentError logs an agent error
func (l *Logger) LogAgentError(agentName, errMsg string) error {
	l.mutex.Lock()
	defer l.mutex.Unlock()

	// Get log file for agent
	logFile, err := l.getLogFile(agentName)
	if err != nil {
		return err
	}

	// Create log entry
	timestamp := time.Now()
	entry := LogEntry{
		Timestamp: timestamp,
		Level:     "ERROR",
		Message:   fmt.Sprintf("Agent %s error: %s", agentName, errMsg),
		Agent:     agentName,
	}

	// Write log entry
	return l.writeLogEntry(logFile, entry)
}

// getLogFile gets (or creates) a log file for the specified agent
func (l *Logger) getLogFile(agentName string) (*os.File, error) {
	// Check if log file already open
	if file, ok := l.logFiles[agentName]; ok {
		return file, nil
	}

	// Create log file
	logPath := filepath.Join(l.logDir, fmt.Sprintf("agent_%s.log", agentName))
	file, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to open log file: %w", err)
	}

	// Store log file
	l.logFiles[agentName] = file

	return file, nil
}

// writeLogEntry writes a log entry to the specified file
func (l *Logger) writeLogEntry(file *os.File, entry LogEntry) error {
	var logLine string
	var err error

	if l.formatJSON {
		// Format as JSON
		data, err := json.Marshal(entry)
		if err != nil {
			return fmt.Errorf("failed to marshal log entry: %w", err)
		}
		logLine = string(data) + "\n"
	} else {
		// Format as plain text
		if entry.Action != "" {
			logLine = fmt.Sprintf("[%s] [%s] [%s] ACTION: %s\n",
				entry.Timestamp.Format(time.RFC3339),
				entry.Level,
				entry.Agent,
				entry.Action)
		} else if entry.Response != "" {
			logLine = fmt.Sprintf("[%s] [%s] [%s] RESPONSE: %s\n",
				entry.Timestamp.Format(time.RFC3339),
				entry.Level,
				entry.Agent,
				entry.Response)
		} else {
			logLine = fmt.Sprintf("[%s] [%s] [%s] %s\n",
				entry.Timestamp.Format(time.RFC3339),
				entry.Level,
				entry.Agent,
				entry.Message)
		}
	}

	// Write log line
	_, err = file.WriteString(logLine)
	return err
}

// Close closes all open log files
func (l *Logger) Close() error {
	l.mutex.Lock()
	defer l.mutex.Unlock()

	var lastErr error
	for _, file := range l.logFiles {
		if err := file.Close(); err != nil {
			lastErr = err
		}
	}

	return lastErr
}
