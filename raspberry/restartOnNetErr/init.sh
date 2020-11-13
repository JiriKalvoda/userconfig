#!/bin/bash
cd "$(dirname "$0")"

sudo ln -sr restartOnNetErr.sh /usr/bin/restartOnNetErr
sudo chmod +x /usr/bin/restartOnNetErr

sudo cp restartOnNetErr.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable restartOnNetErr
