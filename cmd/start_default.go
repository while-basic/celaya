//go:build !windows && !darwin

package cmd

import (
	"context"
	"errors"

	"github.com/celaya/celaya/api"
)

func startApp(ctx context.Context, client *api.Client) error {
	return errors.New("could not connect to ollama server, run 'ollama serve' to start it")
}
