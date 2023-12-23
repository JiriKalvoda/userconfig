#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 1
install_begin

confln notmuch-config ~/.notmuch-config
confln mailcap ~/.mailcap
confln mailcap ~/.mime.types

confln offlineimap-run ~/bin/
g++ offlineimap-deamon.cpp -o ~/bin/offlineimap-deamon -pthread

confln neomuttrc ~/.config/neomutt/
confln color ~/.config/neomutt/ c
confln m ~/bin/
confln m-daemon ~/bin/
confln m-repeat-notification ~/bin/
confln robot-send-mail ~/bin/
confln unzip-mail.py ~/bin/ E
confln vm-mail.sh ~/bin/vmm

r mkdir -p ~/.config/certs
r -bc 'ssh jirikalvoda@kam.mff.cuni.cz cat /etc/ssl/certs/ca-certificates.crt > ~/.config/certs/nikam-ssl.cert'


if [[ ! -L ~/Maildir ]]
then
	confln ~/Maildir-no-dot/INBOX ~/Maildir
fi

(
	cd ~/Maildir-no-dot || exit 1
	for i in *;
	do
		if [[ "$i" != "INBOX" ]] && [[ "$i" != "notmuch" ]]
		then 
			if [[ ! -L INBOX/.$i ]]
			then
				confln $i INBOX/.$i
			fi
		fi
	done 

)

init-service offlineimap "" offlineimap-deamon

install_ok
