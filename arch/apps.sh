aurman -S thunderbird
echo "thunderbird \$@" > ~/bin/start-mail
chmod +x ~/bin/start-mail
aurman -S zoom
aurman -S masterpdfeditor-free
aurman -S qtcreator
sudo pacman -S arandr
aurman -S audacity
aurman -S geogebra-5
sudo pacman -S libreoffice-still
sudo pacman -S gimp
aurman -S xarchiver
sudo pacman -S vlc

sudo pacman -S cronie
systemctl start cronie
systemctl start cronie.service
systemctl enable cronie
systemctl enable cronie.service
aurman -S timeshift




