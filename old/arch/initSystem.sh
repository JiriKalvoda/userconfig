# :map \p <HOME>v<END>y:!<c-R>"<BS><CR>

# set password
passwd root

# update database
pacman -Syu
# update system
pacman -Syy
# I need it to working WIFI
pacman -S linux-firmware
# wifi-menu
pacman -S netctl dialog nmap
# nmtui
pacman -S networkmanager
# basic linux tools
pacman -S base-devel tree
pacman -S wget

# graphic
pacman -S xorg-server xorg-xinit
pacman -S xorg
# fontfs
#pacman -S $(pacman -Sqs ttf| grep '^ttf')
pacman -S ttf-hack ttf-ubuntu-font-family ttf-dejavu ttf-liberation
pacman -S i3
# graphic eviromen i3
pacman -S dmenu 
echo -e "exec i3" > ~/.xinitrc
# terminal emulator
pacman -S rxvt-unicode xsel
pacman -S xclip

# VIM - profesinal tex editor
pacman -S gvim vim-spell-cs
ln /usr/bin/vim /usr/bin/vi -s

# Git - version manager
pacman -S git

# Notification service
pacman -S notify-osd
pacman -S dunst

# SSH - conect to server by shel or git 
pacman -S openssh sshfs

# Web broser
pacman -S chromium

# File manager
pacman -S nemo

# Disk and partition manager
pacman -S gparted
pacman -S gnome-disk-utility
pacman -S baobab

# Proces manager
pacman -S htop

# PDF viewer
pacman -S zathura zathura-pdf-poppler feh

# Image viewer
pacman -S neofetch

# Hinting in bash
pacman -S bash-completion

# Trash file (do not delete)
pacman -S trash-cli

# Power-sawer
pacman -S tlp

# Scripting NumLock
pacman -S numlockx

# Auto mount f.e. USB flash
pacman -S udisks2

# Sound support
pacman -S alsa-lib alsa-utils
pacman -S alsa-oss
pacman -S pavucontrol

# Work with zip files
pacman -S zip unzip

# Opening app by .desktop file
pacman -S xfce4-appfinder exo

# Set time zone
timedatectl set-timezone Europe/Prague

# Screenshots
pacman -S maim

# Sone funny terminal things
pacman -S lolcat cmatrix sl

# Using user bin (executable file) directory 
echo add "\"appendpath '~/bin'\"" to next file
vim /etc/profile
echo "#!/bin/bash\nexport PATH=$PATH:~/bin" > /etc/profile.d/custom.sh
chmod a+x /etc/profile.d/custom.sh

# Intuitiv scrolling
echo add 'Option "NaturalScrolling" "True"' to next file
vim /usr/share/X11/xorg.conf.d/40-libinput.conf

# Init user
echo "\%wheel ALL=(ALL) ALL" >> /etc/sudoers
useradd -m -G wheel jiri
echo -e "dbus-update-activation-env\neval \$(/usr/bin/gnome-keyrecrets,ssh)\nexport SSH_AUTH_SOCK\nexec i3" > /home/jiri/.xinitrc
passwd jiri
#usermod -s jiri

# disable bell
echo "blacklist pcspkr" > /etc/modprobe.d/nobeep.conf

# Mount NTFS write
pacman -S ntfs-3g

pacman -S rsync

##### UNNEED
#pacman -S ttf-dejavu 
#pacman -S ttf-rissole
#pacman -S sudo
#pacman -S gnome-keyring libsecret
## C++ compilator
#pacman -S gcc
#pacman -S --needed base-devel
