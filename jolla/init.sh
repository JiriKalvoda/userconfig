#!/bin/bash
# Hostitelská strana Arch kontejneru na Sailfish OS (sysconfig, root).
# Rootfs kontejneru NEstahuje: ten staví hopik z receptu blach jk-major a
# tlačí ho sem `arch-push VER` (userconfig/jolla/arch-push na hopiku), který
# tu pak spustí `arch-receive VER`; přepnutí je `arch-activate VER`.
#
# Instaluje konfiguraci: bundle, skripty, unitu (enable, bez startu). Jediná
# výjimka je crun: v repu jolla není, tak se stáhne statická binárka z GitHub
# releases (varianta -disable-systemd: cgroupfs, bez vazby na hostitelský
# systemd 238). Balíčky se instalují ručně předem: rsync (cíl rsyncu
# z hopiku), python3 (arch-receive, arch-run), git (userconfig).
cd "$(dirname "$0")"
. ../userconfig-lib.sh
is_sysconfig=true
version 4
need_root
install_begin

# /home/rootfs: jeden fs pro všechny store stromy na telefonu, devices/<name>
# per kontejner (rsync --link-dest může hardlinkovat i napříč zařízeními)
BASE=/home/rootfs/devices/arch-container
BUNDLE=/etc/arch-container
CRUN_VERSION=${CRUN_VERSION:-latest}

for dep in rsync python3 curl; do
	which "$dep" >/dev/null 2>&1 || err "chybí $dep (nainstalovat ručně)"
done

echo -e "${Blue}== crun (statická binárka, v repu jolla není)$None"
if [[ ! -x /usr/local/bin/crun ]]; then
	if [[ "$CRUN_VERSION" == latest ]]; then
		CRUN_VERSION=$(curl -sL https://api.github.com/repos/containers/crun/releases/latest \
			| python3 -c 'import sys,json;print(json.load(sys.stdin)["tag_name"])') || err "nezjistím verzi crun"
	fi
	mkdir -p /usr/local/bin
	r curl -fL -o /usr/local/bin/crun.tmp \
		"https://github.com/containers/crun/releases/download/$CRUN_VERSION/crun-$CRUN_VERSION-linux-arm64-disable-systemd"
	r chmod 755 /usr/local/bin/crun.tmp
	r mv /usr/local/bin/crun.tmp /usr/local/bin/crun
fi
r crun --version

echo -e "${Blue}== adresáře, bundle, skripty, unita$None"
mkdir -p "$BASE/versions" "$BASE/tmp" "$BASE/home" "$BASE/root" "$BASE/hybris-lib" "$BUNDLE"
confln config.json "$BUNDLE/config.json"
for b in bin/*; do
	confln "$b" /usr/local/bin/
done
confln arch-container.service /etc/systemd/system/arch-container.service
r systemctl daemon-reload
r systemctl enable arch-container.service

install_ok
echo
echo "Služba je povolená, ale nespuštěná. Dál z hopiku:"
echo "  userconfig/jolla/arch-push v1 -a     # rsync sem, arch-receive, arch-activate (= restart služby)"
