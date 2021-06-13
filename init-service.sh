#!/bin/bash
name="$1"
user="$2"
exe="$3"
par="$4"
opt="$5"

if [ -z "$name" ] || [ -z "$user" ] || [ -z "$exe" ]
then 
	echo "Script for creating systemd deamon"
	echo "Usage:"
	echo "	$0 name user exec [cmd parametrs] [daemon options]"
	exit 100
fi

if id "$user" &>/dev/null; then  true ; else
    echo "user $user not found"
	exit 1
fi

home="$(getent passwd "$user" | cut -d: -f6)"
path="/usr/local/sbin:/usr/local/bin:/usr/bin:$home/bin"
if [[ "$exe" == "/"* ]]
then
	exePath="$exe"
else
	exePath="$(PATH=$path which $exe)"
fi

[ -z "$exePath" ] && exit 2

tmp=$(mktemp)

cat > $tmp <<EOF
[Unit]
Description=$name
After=network.target

[Service]
User=$user
Environment=HOME=$home
Environment=PATH=$path
ExecStart=$exePath $par
Restart=on-failure
$opt

[Install]
WantedBy=multi-user.target
EOF




confln $tmp /lib/systemd/system/$name.service cr
systemctl daemon-reload

if [[ "$opt" != *d* ]]
then
	systemctl enable $name
	systemctl restart $name
fi

rm $tmp
