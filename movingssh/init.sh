#!/bin/bash
cd "$(dirname "$0")"

sudo cp movingssh /usr/bin/
sudo chmod +x movingssh
mkdir -p ~/.movingssh
