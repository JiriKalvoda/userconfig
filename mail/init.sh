#!/bin/bash
cd "$(dirname "$0")"

sudo ln -sr offlineimap-run /usr/bin
sudo g++ offlineimap-deamon.cpp -o /usr/bin/offlineimap-deamon -pthread

sudo cp offlineimap-jiri.service /lib/systemd/system
sudo ln -sr mailcap /etc/
sudo systemctl daemon-reload
sudo systemctl enable offlineimap-jiri

mkdir -p ~/.config/neomutt
ln -sr neomuttrc ~/.config/neomutt/
ln -sr m ~/bin
ln -sr m-daemon ~/bin


ln -sr ~/Maildir-no-dot/INBOX ~/Maildir
(
	cd ~/Maildir-no-dot
	for i in *;
	do
		if [[ "$i" != "INBOX" ]]
		then 
			unlink $i/$i 
			unlink INBOX/$i 

			if [[ ! -L INBOX/.$i ]]
			then
				ln -sr $i INBOX/.$i
			fi
		fi
	done 

)
