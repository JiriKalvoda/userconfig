#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 6
install_begin

confln main.km ~/.config/i3/config-gen
confln led-cmddef.km ~/.config/i3/
confln led-blatto-1.km ~/.config/i3/
confln led-blatto-sp.km ~/.config/i3/
confln ssh-cmddef.km ~/.config/i3/
confln xrandr-cmddef.km ~/.config/i3/

(
	cd ~/.config/i3
	r mkdir -p ../sway
	r -b './config-gen > config'
	r -b './config-gen sway > ../sway/config'
	r -b './config-gen sway vncserver > ../sway/vnc.config'
)

install_ok
