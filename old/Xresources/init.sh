#!/bin/bash
cd "$(dirname "$0")"

confln new-window ~/.urxvt/ext/new-window
confln close-gracefully ~/.urxvt/ext/close-gracefully
confln Xresources ~/.Xresources

xrdb  ~/.Xresources
