#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln x ~/bin/
confln plugins/jk ~/.config/xournalpp/plugins/

install_ok
