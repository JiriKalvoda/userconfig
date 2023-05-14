#!/bin/bash
. ../userconfig-lib.sh

confln jk-Alpha.svg ~/.local/share/onboard/layouts/images/
confln jk-Numpad.svg ~/.local/share/onboard/layouts/images/
confln jk.onboard ~/.local/share/onboard/layouts/images/

r -cb dconf 'load /org/onboard/ < dconf.ini'
