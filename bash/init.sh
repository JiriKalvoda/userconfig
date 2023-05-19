#!/bin/bash
. ../userconfig-lib.sh
install_begin

confln bashrc ~/.bashrc
confln bash_profile ~/.bash_profile
confln wd ~/bin/
r mkdir -p ~/bin/bashrc
