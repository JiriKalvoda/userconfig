#!/bin/bash
cd "$(dirname "$0")"

confln mailcap ~/.mailcap

confln offlineimap-run ~/bin/
g++ offlineimap-deamon.cpp -o ~/bin/offlineimap-deamon -pthread

confln neomuttrc ~/.config/neomutt/
confln color ~/.config/neomutt/ c
confln m ~/bin/
confln m-daemon ~/bin/
confln m-daemon ~/bin/
confln m-repeat-notification ~/bin/

confln robot-send-mail ~/bin/


if [[ ! -L ~/Maildir ]]
then
	confln ~/Maildir-no-dot/INBOX ~/Maildir
fi

(
	cd ~/Maildir-no-dot || exit 1
	for i in *;
	do
		if [[ "$i" != "INBOX" ]]
		then 
			# unlink $i/$i 
			# unlink INBOX/$i 

			if [[ ! -L INBOX/.$i ]]
			then
				confln $i INBOX/.$i
			fi
		fi
	done 

)
