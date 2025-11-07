#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln keybindings.json ~/.config/VSCodium/User/
confln settings.json ~/.config/VSCodium/User/

install_ok
