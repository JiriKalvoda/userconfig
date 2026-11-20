#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln jk_config.kdl ~/.config/tripscope/

install_ok
