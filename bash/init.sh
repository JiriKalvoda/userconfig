#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln bashrc ~/.bashrc
confln bash_profile ~/.bash_profile
confln wd ~/bin/
r mkdir -p ~/bin/bashrc

install_ok
