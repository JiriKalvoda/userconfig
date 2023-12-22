#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln config.rasi ~/.config/rofi/

install_ok
