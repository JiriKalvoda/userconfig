#!/bin/bash
cd "$(dirname "$0")"

g++ powerbutton.cpp -o /usr/bin/powerbutton -lwiringPi

cp powerbutton.service /lib/systemd/system
systemctl daemon-reload
systemctl enable powerbutton

