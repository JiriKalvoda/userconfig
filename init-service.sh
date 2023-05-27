#!/bin/bash
switches=""
while [[ "$1" == "-"* ]] && [[ "$1" != "--"* ]]
do
	switches="$switches$1"
	shift
done

name="$1"
user="${2:---user}"
exe="$3"
par="$4"
opt="$5"
installToUser=False

if [ -z "$name" ] || [ -z "$user" ] || [ -z "$exe" ]
then 
	echo "Script for creating systemd deamon"
	echo "Usage:"
	echo "	$0 name [-d] [user/'--user'] exec [cmd parametrs] [daemon options]"
	exit 100
fi

if [[ "$user" == "--user" ]]
then
	user="$USER"
	installToUser=true
	# loginctl enable-linger USERNAME
fi

if $installToUser
then
	systemctlUserArg="--user"
fi

if id "$user" &>/dev/null; then  true ; else
    echo "user $user not found"
	exit 1
fi

home="$(getent passwd "$user" | cut -d: -f6)"
path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/sbin:/usr/bin:/bin:$home/bin"
if [[ "$exe" == "/"* ]]
then
	exePath="$exe"
else
	exePath="$(PATH=$path which $exe)"
fi

[ -z "$exePath" ] && exit 2

tmp=$(mktemp)

if $installToUser
then
lineUser=""
else
lineUser="User=$user"
fi

if $installToUser
then
lineWantedBy="WantedBy=default.target"
else
lineWantedBy="WantedBy=multi-user.target"
fi

cat > $tmp <<EOF
[Unit]
Description=$name
After=network.target

[Service]
$lineUser
Environment=HOME=$home
Environment=PATH=$path
ExecStart=$exePath $par
Restart=always
RestartSec=10
$opt

[Install]
$lineWantedBy
EOF


systemctl $systemctlUserArg disable $name


if $installToUser
then
	confln $tmp ~/.config/systemd/user/$name.service cr
else
	confln $tmp /lib/systemd/system/$name.service cr
fi
systemctl $systemctlUserArg daemon-reload

if [[ "$switches" != *d* ]]
then
	systemctl $systemctlUserArg enable $name
	systemctl $systemctlUserArg restart $name
fi

rm $tmp
