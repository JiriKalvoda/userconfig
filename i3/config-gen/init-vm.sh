#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 2
install_begin

confln main.km ~/.config/i3/config-gen
confln xrandr-cmddef.km ~/.config/i3/

(
	cd ~/.config/i3
	r mkdir -p ../sway
	r -b './config-gen > config'
	r -b './config-gen sway > ../sway/config'
	r -b './config-gen sway vncserver > ../sway/vnc.config'
)

install_ok
