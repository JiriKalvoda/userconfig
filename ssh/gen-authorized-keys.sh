#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh

set -ueo pipefail

need_state_server


catuniq()
{
	cat "$@" | sort -u |(
		while read -r line
		do
			num=999
			name="$( echo "$line" | cut -d' ' -f4)"
			user="$( echo "$name" | cut -d'@' -f1)"
			host="$( echo "$name" | cut -d'@' -f2)"
			echo $user $host $num >/dev/stderr
			[[ $host == arch ]] && num=001
			[[ $host == arzen ]] && num=002
			[[ $host == phone ]] && num=101
			[[ $host == samet ]] && num=102
			[[ $host == external ]] && num=301
			[[ $host == "rpi*" ]] && num=400
			[[ $host == "hluk" ]] && num=521
			[[ $host == "teplo" ]] && num=531
			[[ $host == "kam" ]] && num=601
			[[ $host == "gimli" ]] && num=602
			[[ $host == "ucw" ]] && num=611
			echo -n $num ""
			echo "$line"
		done
	)| sort | cut -d' ' -f2-
}
catuniq $userconfig_state_server/*/state/ssh-init-private-keys.sh/last_ok/files/id_ed25519.pub > keys_normal
catuniq $userconfig_state_server/*/state/ssh-init-private-keys.sh/last_ok/files/id_ed25519_secret.pub > keys_secret
catuniq $userconfig_state_server/*/state/ssh-init-private-keys.sh/last_ok/files/id_ed25519_secret.pub > keys_trash

cat keys_secret > authorized_keys_secret

(
	cat keys_normal
	echo
	cat keys_secret
) > authorized_keys

git diff .
echo please commit changes
