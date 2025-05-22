//go:build !windows

package tray

import (
	"errors"

	"github.com/celaya/celaya/app/tray/commontray"
)

func InitPlatformTray(icon, updateIcon []byte) (commontray.OllamaTray, error) {
	return nil, errors.New("not implemented")
}
