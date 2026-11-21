#!/bin/bash
# The sync server's own on the data disk, made before it starts (its
# ExecStartPre, as root, after the disk's mount): its directory and, at the
# first start, its certificate — self-signed: the clients pin it (the pin
# in the journal, or `tripscope-sync-server --pin
# /data/tripscope-sync/cert.pem`).
set -eu
d=/data/tripscope-sync
install -d -m 700 -o tripscope -g tripscope "$d"
if [[ ! -f $d/key.pem ]]; then
	openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 36500 \
		-subj /CN=tripscope-sync -keyout "$d/key.pem" -out "$d/cert.pem"
	chown tripscope:tripscope "$d/key.pem" "$d/cert.pem"
	chmod 600 "$d/key.pem"
	echo "nový certifikát, pin=\"$(/usr/local/bin/tripscope-sync-server --pin "$d/cert.pem")\""
fi
