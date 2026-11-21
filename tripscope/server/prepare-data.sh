#!/bin/bash
# The data server's directories on the data disk, made (and their owners
# and modes set again) before it starts: its ExecStartPre, as root, after
# the disk's mount.
set -eu
d=/data/tripscope

# the chroot of the account data (sshd.conf): export/ and above root's,
# writable by none else — sshd refuses it otherwise
install -d -m 755 -o root -g root "$d" "$d/export"
# the service's own: the archive and the published tree, its state
install -d -m 755 -o tripscope -g tripscope "$d/export/archive" "$d/export/pub"
install -d -m 750 -o tripscope -g tripscope "$d/state"
