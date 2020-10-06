# disable pacman key signature checking
# /etc/pacman.conf : SigLevel = Never

pacman -Syu

# Keyring 
pacman -S haveged
pacman -S archlinux-keyring
systemctl start haveged
systemctl enable haveged
rm -fr /etc/pacman.d/gnupg
pacman-key --init
pacman-key --populate archlinux

# Then enable

# Silent boot
sed -i ' 1 s/.*/& quiet vga=current /' cmdline.txt

useradd -m kachlicka
useradd -m jiri

pacman -S sudo git gvim vim-spell-cs htop bash-completion linux-firmware netcat dialog networkmanager ethtool
ln /usr/bin/vim /usr/bin/vi -s




