#!/bin/bash
# Běží při BUILDU uvnitř Arch Linux ARM stromu (rootfs exec root=fs, přes
# qemu-user), jako sysconfig balíček userconfig.jolla_container (blach jk.py:
# major). Dělá z holého Archu systém pro crun kontejner na Sailfish OS:
# sdílený kernel, /dev, /sys, síť a UTS s hostitelem, GUI přes Lipstick.
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
is_sysconfig=true
version 1
need_root
install_begin

echo -e "${Blue}== služby, které by se praly s hostitelem$None"
# sdílený kernel (sysctl, binfmt, moduly, rfkill, pstore), sdílený /dev a
# /sys (udev, tmpfiles-dev, getty na hostitelských tty), sdílená síť
# (networkd, resolved), logind (sessions a /run/user patří hostiteli)
mask_units="
systemd-udevd.service systemd-udevd-control.socket systemd-udevd-kernel.socket
systemd-udev-trigger.service systemd-udev-settle.service systemd-hwdb-update.service
systemd-networkd.service systemd-networkd.socket systemd-networkd-wait-online.service
systemd-resolved.service systemd-timesyncd.service systemd-logind.service
systemd-modules-load.service kmod-static-nodes.service systemd-sysctl.service
systemd-binfmt.service systemd-rfkill.service systemd-rfkill.socket
systemd-vconsole-setup.service systemd-firstboot.service systemd-pstore.service
systemd-journald-audit.socket
systemd-tmpfiles-setup-dev-early.service systemd-tmpfiles-setup-dev.service
getty.target getty@tty1.service console-getty.service serial-getty@.service
systemd-ask-password-console.service systemd-ask-password-wall.service
sys-kernel-config.mount sys-kernel-debug.mount sys-kernel-tracing.mount
dev-hugepages.mount dev-mqueue.mount sys-fs-fuse-connections.mount
proc-sys-fs-binfmt_misc.automount proc-sys-fs-binfmt_misc.mount
"
mkdir -p /etc/systemd/system
for u in $mask_units; do
	ln -sfn /dev/null /etc/systemd/system/$u
done
# systémový D-Bus uvnitř (co dělá `systemctl enable dbus-broker`; pacman hook
# v build chrootu presety přeskočí)
wants=/etc/systemd/system/multi-user.target.wants
mkdir -p $wants
ln -sf /usr/lib/systemd/system/dbus-broker.service $wants/
ln -sf /usr/lib/systemd/system/dbus-broker.service /etc/systemd/system/dbus.service

echo -e "${Blue}== hostname: UTS namespace je hostitelův$None"
r rm -f /etc/hostname

echo -e "${Blue}== uživatel defaultuser (uid 100000 jako na Sailfish)$None"
# gid z hostitele (Sailfish OS 5.2, droid-hal): zařízení v /dev patří těmto
# skupinám; defaultuser v nich na hostiteli je, tak i tady
host_groups="video:39 audio:1005 graphics:1003 input:1004 system:1000"
getent group defaultuser >/dev/null || r groupadd -g 100000 defaultuser
if ! id defaultuser &>/dev/null; then
	# bez -m: /home/defaultuser je za běhu bind hostitelského
	# /home/rootfs/devices/arch-container/home
	# (persistentní, mimo overlay); kostru tam dá arch-run při prvním startu
	r useradd -u 100000 -g 100000 -M -s /bin/bash defaultuser
fi
mkdir -p /home/defaultuser
for spec in $host_groups; do
	name=${spec%%:*}; gid=${spec##*:}
	getent group "$gid" >/dev/null || r groupadd -g "$gid" "sfos-$name"
	r usermod -aG "$(getent group "$gid" | cut -d: -f1)" defaultuser
done
r passwd -d root

echo -e "${Blue}== locale$None"
grep -q '^en_US.UTF-8' /etc/locale.gen || echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen
grep -q '^cs_CZ.UTF-8' /etc/locale.gen || echo 'cs_CZ.UTF-8 UTF-8' >> /etc/locale.gen
r -P locale-gen
[[ -f /etc/locale.conf ]] || echo 'LANG=en_US.UTF-8' > /etc/locale.conf

echo -e "${Blue}== soubory$None"
confln files/sfos.sh /etc/profile.d/sfos.sh
confln files/journald-sfos.conf /etc/systemd/journald.conf.d/sfos.conf
confln files/hybris /usr/local/bin/hybris
# libhybris má zakompilovanou cestu k platform pluginům /usr/lib64/libhybris
# (Arch: /usr/lib64 -> lib); /opt/hybris/lib plní za běhu bind z hostitele
mkdir -p /opt/hybris
[[ -e /usr/lib/libhybris ]] || r ln -s /opt/hybris/lib/libhybris /usr/lib/libhybris
mkdir -p /sfos/home /sfos/lib64 /opt/hybris/lib

echo -e "${Blue}== úklid /run$None"
# build chroot nemá na /run tmpfs, takže co si tam systemd nástroje z pacman
# hooků odložily (run/systemd/dissect-root), by skončilo v obrazu; za běhu je
# /run tmpfs z crun
find /run -mindepth 1 -delete 2>/dev/null || true

install_ok
