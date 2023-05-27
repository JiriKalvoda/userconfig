#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

init-service publicmyip "$1" publicmyip

install_ok

