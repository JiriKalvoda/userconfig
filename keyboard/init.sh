#!/bin/bash
cd "$(dirname "$0")"

cp /usr/share/X11/xkb/symbols/cz /usr/share/X11/xkb/symbols/cz_backup`date +%s`
cp cz /usr/share/X11/xkb/symbols/cz

cp keyboard.conf /etc/X11/xorg.conf.d/00-keyboard.conf

