#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln mimeapps.list ../../.config/mimeapps.list

install_ok

