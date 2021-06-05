#!/bin/bash
cd "$(dirname "$0")"

confln wacom-config ~/bin
gcc wacom-daemon2.c -o ~/bin/wacom-daemon -lxdo
