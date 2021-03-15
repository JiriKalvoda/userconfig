#!/bin/bash
cd "$(dirname "$0")"

sudo chmod +x suspender
sudo ln -sr suspender /usr/bin/
