#!/bin/bash
cd "$(dirname "$0")"

sudo g++ powerbutton.cpp -o /usr/bin/powerbutton -lwiringPi

sudo cp powerbutton.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable powerbutton

