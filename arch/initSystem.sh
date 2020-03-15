# :map \p <HOME>v<END>y:!<c-R>"<BS><CR>
pacman -Syu
pacman -Syy
pacman -S nmtui
pacman -S base-devel
pacman -S i3
pacman -S xorg-server xorg-xinit
pacman -S xorg
pacman -S $(pacman -Qqs ttf)
pacman -S ttf-dejavu 
pacman -S ttf-rissole
pacman -S dmenu 
pacman -S rxvt-unicode xsel
pacman -S xclip
pacman -S gvim vim-spell-cs
cp /usr/bin/vim /usr/bin/vi
pacman -S git
pacman -S gcc
pacman -S notify-osd
pacman -S openssh
pacman -S chromium
pacman -S nemo
pacman -S gparted
pacman -S gnome-disk-utility
pacman -S texlive-core
pacman -S zathura zathura-pdf-poppler
pacman -S wget
pacman -S baobab
pacman -S htop
pacman -S gnome-keyring libsecret
pacman -S numlockx
pacman -S bash-completion
pacman -S trash-cli
pacman -S neofetch
pacman -S dunst
pacman -S alsa-lib alsa-utils
pacman -S alsa-oss
pacman -S tlp
pacman -S zip unzip
pacman -S aradar
pacman -S --needed base-devel
timedatectl set-timezone Europe/Prague
echo -e "exec i3" > ~/.xinitrc
pacman -S lolcat cmatrix 
pacman -S sudo
echo add "\"appendpath '~/bin'\"" to next file
vim /etc/profile
echo add 'Option "NaturalScrolling" "True"' to next file
vim /usr/share/X11/xorg.conf.d/40-libinput.conf
echo "\%wheel ALL=(ALL) ALL" >> /etc/sudoers
useradd -m -s -G wheel jiri
echo -e "dbus-update-activation-env\neval \$(/usr/bin/gnome-keyrecrets,ssh)\nexport SSH_AUTH_SOCK\nexec i3" > /home/jiri/.xinitrc

echo "blacklist pcspkr" > /etc/modprobe.d/nobeep.conf
usermod -s jiri
passwd jiri

