#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
install_begin

confln main.km ~/.config/i3/config-gen

(
	cd ~/.config/i3
	./config-gen > config
)

install_ok
