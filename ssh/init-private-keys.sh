#!/bin/bash
. ../userconfig-lib.sh
install_begin

date=$(date +%Y-%m-%d)

default_places=$USER@$(hostname)
echo -n set places "(default $default_places):"
read places
[[ $places == "" ]] && places=default_places

new_dir=~/.ssh/new
[[ -d $new_dir ]] && r rm -r $new_dir
r mkdir -p $new_dir

r ssh-keygen -t ed25519 -C "jirikalvoda@ucw.cz $places secret $date" -f $new_dir/id_ed25519_secret
r ssh-keygen -t ed25519 -C "jirikalvoda@ucw.cz $places normal $date" -f $new_dir/id_ed25519 -N ""
r ssh-keygen -t ed25519 -C "jirikalvoda@ucw.cz $places trash $date" -f $new_dir/id_ed25519_trash -N ""

confln $new_dir/id_ed25519_secret ~/.ssh/ c
confln $new_dir/id_ed25519 ~/.ssh/ c
confln $new_dir/id_ed25519_trash ~/.ssh/ c

confln $new_dir/id_ed25519_secret.pub ~/.ssh/ c
confln $new_dir/id_ed25519.pub ~/.ssh/ c
confln $new_dir/id_ed25519_trash.pub ~/.ssh/ c

r cp ~/.ssh/*.pub  $state_run_dir/files/

r rm -r $new_dir

install_ok
