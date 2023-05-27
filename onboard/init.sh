#!/bin/bash
. ../userconfig-lib.sh

confln jk-Alpha.svg ~/.local/share/onboard/layouts/
confln jk-Numpad.svg ~/.local/share/onboard/layouts/
confln jk.onboard ~/.local/share/onboard/layouts/

r -cb dconf 'load /org/onboard/ < dconf.ini'
