sudo cp /usr/share/X11/xkb/symbols/cz /usr/share/X11/xkb/symbols/cz_backup`date +%s`
sudo cp cz /usr/share/X11/xkb/symbols/cz
echo setxkbmap us,cz -variant ,ucw -option grp:caps_switch >> ~/.profile

