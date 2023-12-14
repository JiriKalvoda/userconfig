#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
need_root
install_begin

r g++ ./volumeInfo.c -o /usr/bin/volumeInfo
r chmod u+s /usr/bin/volumeInfo
r cp ./volumeGUI.sh  /usr/bin/volumeGUI
r chmod o+x /usr/bin/volumeGUI

install_ok
