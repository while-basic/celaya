package tray

import (
	"github.com/celaya/celaya/app/tray/commontray"
	"github.com/celaya/celaya/app/tray/wintray"
)

func InitPlatformTray(icon, updateIcon []byte) (commontray.OllamaTray, error) {
	return wintray.InitTray(icon, updateIcon)
}
