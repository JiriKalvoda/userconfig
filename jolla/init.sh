#!/bin/bash
# Hostitelská strana Arch kontejneru na Sailfish OS (sysconfig, root).
# Rootfs kontejneru NEstahuje: ten staví builder z receptu blach jk-major a
# tahá se přes `arch-fetch VER` + `arch-activate VER`.
# Předpoklady: userconfig v /etc/userconfig, git, curl, python3, rsync, ssh klíč
# roota na builder.
cd "$(dirname "$0")"
. ../userconfig-lib.sh
is_sysconfig=true
version 2
need_root
install_begin

BASE=/home/arch
BUNDLE=/etc/arch-container
CRUN_VERSION=${CRUN_VERSION:-latest}

which rsync >/dev/null || r pkcon install -y rsync

echo -e "${Blue}== crun (statická binárka)$None"
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
confln fetch.conf "$BUNDLE/fetch.conf"
for b in bin/*; do
	confln "$b" /usr/local/bin/
done
confln arch-container.service /etc/systemd/system/arch-container.service
r systemctl daemon-reload
r systemctl enable arch-container.service

install_ok
echo
if [[ -L $BASE/current ]]; then
	r systemctl restart arch-container.service
else
	echo "Zatím není žádná verze. Dál:"
	echo "  arch-fetch -l            # co je na builderu"
	echo "  arch-fetch v1 && arch-activate v1"
fi
