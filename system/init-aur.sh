#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

if id aur
then
	echo User yar yet exists, skipping
else
	r useradd --create-home --home-dir /var/cache/aur --uid 1100 aur
fi

r su aur -c "../git-clupdate https://aur.archlinux.org/yay.git /var/cache/aur/yay"

for x in /var/cache/aur/yay/*.pkg.tar.zst
do
	if [[ -f $x ]]
	then
		r rm $x
	fi
done


r su aur -c "cd ~/yay && makepkg"
r -P pacman -U /var/cache/aur/yay/yay-*.pkg.tar.zst

#date=$(date +%Y-%m-%d)
#[[ -f  /var/cache/aur/.ssh/id_ed25519 ]] || r su aur  -c "ssh-keygen -t ed25519 -C \"aur@$(hostname)  $date\"  -N \"\" -f /var/cache/aur/.ssh/id_ed25519"

confln aur-sudo /etc/sudoers.d/aur r
install_ok
