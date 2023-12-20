#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
install_begin

confln main.km ~/.config/i3/config-gen
confln led-cmddef.km ~/.config/i3/
confln led-jug9-1.km ~/.config/i3/
confln ssh-cmddef.km ~/.config/i3/
confln xrandr-cmddef.km ~/.config/i3/

(
	cd ~/.config/i3
	r -b './config-gen > config'
)

install_ok
