#!/bin/bash
cd "$(dirname "$0")"

sudo cp /usr/share/X11/xkb/symbols/cz /usr/share/X11/xkb/symbols/cz_backup`date +%s`
sudo cp cz /usr/share/X11/xkb/symbols/cz

