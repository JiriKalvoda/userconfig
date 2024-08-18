#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 1
install_begin

confln mw2md.sh ~/bin/mw2md
confln tvim.sh ~/bin/tvim
confln booklet.sh ~/bin/booklet
confln lpbooklet.sh ~/bin/lpbooklet
confln pub ~/bin/
confln vzt.sh ~/bin/vzt

confln sfs.py ~/bin/ E

install_ok
