#!/bin/bash
cd "$(dirname "$0")"

confln main.km ~/.config/i3/config-gen
confln led-cmddef.km ~/.config/i3/
confln led-jug9-1.km ~/.config/i3/

(
	cd ~/.config/i3
	./config-gen > config
)

