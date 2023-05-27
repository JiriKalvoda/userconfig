#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh

action="$1"
 if [[ "$action" == "" ]]
then
	err No action
fi

install_begin


date=$(date +%Y-%m-%d)

get_place()
{
	default_places=$USER@$(hostname)
	echo -n set places "(default $default_places):"
	read places
	[[ $places == "" ]] && places=$default_places
}

conflnall(){
	confln $1/id_ed25519_secret ~/.ssh/ c
	confln $1/id_ed25519 ~/.ssh/ c
	confln $1/id_ed25519_trash ~/.ssh/ c

	confln $1/id_ed25519_secret.pub ~/.ssh/ c
	confln $1/id_ed25519.pub ~/.ssh/ c
	confln $1/id_ed25519_trash.pub ~/.ssh/ c
}


if [[ "$action" == "gen" ]]
then
	get_place
	new_dir=~/.ssh/new
	[[ -d $new_dir ]] && r rm -r $new_dir
	r mkdir -p $new_dir
	r ssh-keygen -t ed25519 -C "jirikalvoda@ucw.cz $places secret $date" -f $new_dir/id_ed25519_secret
	r ssh-keygen -t ed25519 -C "jirikalvoda@ucw.cz $places normal $date" -f $new_dir/id_ed25519 -N ""
	r ssh-keygen -t ed25519 -C "jirikalvoda@ucw.cz $places trash $date" -f $new_dir/id_ed25519_trash -N ""
	conflnall $new_dir
	r rm -r $new_dir
elif [[ "$action" == "copy" ]]
then
	[[ "$2" == "" ]] && err Missing argument
	conflnall $2
elif [[ "$action" == "ssh" ]] || [[ "$action" == ms ]] || [[ "$action" == movingssh ]]
then
	new_dir=~/.ssh/new
	[[ -d $new_dir ]] && r rm -r $new_dir
	r mkdir -p $new_dir
	for i in id_ed25519{_secret,,_trash},{,.pub}
	do
		r -b "$(print " %q") cat .ssh/$i > $new_dir/$i"
	done
	conflnall $new_dir
	r rm -r $new_dir
elif [[ "$action" == "none" ]]
then
	:
else
	err Wrong action
fi



r cp ~/.ssh/*.pub  $state_run_dir/files/


echo
echo
cat  ~/.ssh/*pub
echo
echo

install_ok
