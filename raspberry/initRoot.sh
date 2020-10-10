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

echo >> /etc/locale.gen  en_US.UTF-8 UTF-8
sudo locale-gen
echo > /etc/locale.conf LANG=en_US.UTF-8
echo >> /etc/locale.conf LC_COLLATE=C


# Silent boot
sed -i ' 1 s/.*/& quiet vga=current /' cmdline.txt

useradd -m kachlicka
useradd -m jiri

pacman -S sudo git gvim vim-spell-cs htop bash-completion linux-firmware netcat dialog networkmanager ethtool python python-pip
pacman -S i2c-tools lm_sensors
pip install RPi.GPIO
ln /usr/bin/vim /usr/bin/vi -s

pip install -U pip setuptools

aurman -S wiringpi
#sudo pacman -S pcbdraw



