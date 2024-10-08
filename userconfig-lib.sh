Red="\e[31m"
Green="\e[32m"
Yellow="\e[33m"
Blue="\e[34m"
Magenta="\e[35m"
None="\e[0m"

export CONFLN_DATE=${CONFLN_DATE:-$(date +%Y-%m-%d--%H-%M-%S)}

if [[ "$USERCONFIG_ROOT" == "" ]]
then
	USERCONFIG_ROOT=$(git rev-parse --show-toplevel)
	[[ $? != 0 ]] && exit 1
fi

if ! grep jdskjcnjknksncfdvvndfiuvifd $USERCONFIG_ROOT/userconfig-lib.sh >/dev/null
then
	echo "$USERCONFIG_ROOT don't look like userconfig git root."
	exit 1
fi

version(){
	version=$1
}
default_version(){
	[[ "$version" == "" ]] && version 0
}

err()
{
	echo -en $Red
	echo -n ERROR $@
	echo -en $None
	echo
	if [[ "${state_run_dir:-}" != "" ]]
	then
		echo faild > $state_run_dir/state
		echo $@ > $state_run_dir/error
		echo -e "${Blue}INSTALL FAIL $install_name$None"
	fi
	exit 1
}

need_root()
{
	default_version
	if [[ $UID != 0 ]]
	then
		echo -e "\e[31mROOT REQUIRE\e[0m"
		exit 1
	fi
	echo -e "\e[32mROOT REQUIRE\e[0m"
}

confln()
{
	$USERCONFIG_ROOT/confln "$@" || err confln faild
}

init-service()
{
	(
		. $USERCONFIG_ROOT/init-service.sh "$@"
	) || err init-service faild
}

git_clupdate()
{
	if [[ -d $2 ]]
	then
		(cd $2 ; git pull $1)
	else
		git clone $1 $2
	fi
}

r_exit_on_err=true
r_pipe_output=true
r_confirm=false

r()
{
	# Run commant with nice log
	#
	exit_on_err=$r_exit_on_err
	pipe_output=$r_pipe_output
	confirm=$r_confirm
	do_eval=false
	while [[ "$1" == "-"* ]]
	do
		if [[ "$1" == *b* ]]; then do_eval=true; fi
		if [[ "$1" == *B* ]]; then do_eval=false; fi
		if [[ "$1" == *c* ]]; then confirm=true; fi
		if [[ "$1" == *C* ]]; then confirm=false; fi
		if [[ "$1" == *e* ]]; then exit_on_err=true; fi
		if [[ "$1" == *E* ]]; then exit_on_err=false; fi
		if [[ "$1" == *p* ]]; then pipe_output=true; fi
		if [[ "$1" == *P* ]]; then pipe_output=false; fi
		if [[ "$1" == "-" ]] || [[ "$1" == "--" ]]
		then
			break
		fi
		shift
	done

	echo -n ">" 
	if $do_eval
	then
		echo "" "$@"
	else
		printf " %q" "$@"
		echo
	fi

	if $confirm
	then
		in=""
		while [[ "$in" != y ]]
		do
			echo -n -e " ╞ $Yellow Run?(Yes/Skip/Exit):$None "
			read -n 1 in
			echo
			[[ "$in" == "e" ]] && echo -e " └─  $Magenta Without run (exit) \e[0m" && exit 1
			[[ "$in" == "s" ]] && echo -e " └─  $Magenta Without run (skip) \e[0m" && return 0
		done
	fi

	if $pipe_output
	then
		(
			if $do_eval
			then
				eval "$@"
			else
				"$@"
			fi
		) 2>&1 | (
			while read l
			do
				echo " │ $l"
			done
		)
		ret="${PIPESTATUS[0]}"
	else
		if $do_eval
		then
			eval "$@"
			ret="$?"
		else
			"$@"
			ret="$?"
		fi
	fi
	if [[ "$ret" == 0 ]]
	then
		echo -e " └─   \e[32mOK\e[0m"
	else
		if $exit_on_err
		then
			echo -e " └─   \e[31mRETURNED $ret => EXIT\e[0m"
			err subprocess faild
		else
			echo -e " └─   \e[31mRETURNED $ret\e[0m"
		fi
	fi
	return $ret
}

install_try_push(){
	$USERCONFIG_ROOT/state_push.sh
}

install_config_load(){
	install_config_path=$USERCONFIG_ROOT/state/install_config
	mkdir -p $USERCONFIG_ROOT/state
	if [[ ! -f $install_config_path ]]
	then
		echo -e "${Red}No install config, creating${None}"
		(
			echo "ic_version=0"
			echo "ic_name=$([[ "$(pwd)" == /etc/* ]] &&  echo SYS || echo "$USER")@$(hostname)"
			echo "ic_push='ssh jirikalvoda@ucw.cz'"
			echo "ic_pull='movingssh -xd $USER@$(hostname)'"
			echo "ic_userconfig_path='$(cd $USERCONFIG_ROOT ; pwd)'"
			echo "ic_sysconfig='$([[ "$(pwd)" == /etc/* ]] &&  echo true || echo false)'"
		) > $install_config_path
		vim $install_config_path || exit 1
	fi
	ic_sysconfig=false
	. $install_config_path
}

reln(){
	[[ -h $2 ]] && (rm $2 || err rm faild)
	ln -sr $1 $2 || err reln faild
}

clean_userinstall(){
	if [[ -e ~/userconfig/state/$install_name/last ]]
	then
		echo -e "${Blue}Removing userconfig installation${None}"
		rm ~/userconfig/state/$install_name/last
		rm ~/userconfig/state/$install_name/last_ok
		bash <<AMEN
			cd ~/userconfig
			. userconfig-lib.sh
			install_try_push
AMEN
	fi
}
install_begin(){
	is_sysconfig=${is_sysconfig:-false}
	default_version
	install_config_load
	if $ic_sysconfig && ! $is_sysconfig
	then
		err "This script should be called only from userconfig"
	fi
	if ! $ic_sysconfig && $is_sysconfig
	then
		err "This script should be called only from sysconfig"
	fi
	if [[ "$install_name" ==  "" ]]
	then
		install_name=$(pwd)/$(basename $0)
		install_name=${install_name#$USERCONFIG_ROOT/}
		[[ "$install_name" == *"/init.sh" ]] && install_name=${install_name%/init.sh}
		install_name=${install_name//\//-}
	fi
	state_dir=$USERCONFIG_ROOT/state/$install_name
	state_run_dir=$state_dir/$(date +%Y-%m-%d--%H-%M-%S)
	mkdir -p $state_dir
	if [[ -e $state_run_dir ]]
	then
		state_run_dir=""
		err "State run dir exist, wait a second"
		exit 1
	fi
	mkdir -p $state_run_dir
	mkdir -p $state_run_dir/files
	echo -e "${Blue}INSTALLING $install_name$None (version $version)"
	echo $version > $state_run_dir/version
	echo installing > $state_run_dir/state
	printf "%s" "$global_args" > $state_run_dir/args
	date -Iseconds > $state_run_dir/date
	git rev-parse --verify HEAD > $state_run_dir/commit
	git diff > $state_run_dir/git_diff
	reln $state_run_dir $state_dir/last
}

install_ok(){
	echo  ok > $state_run_dir/state
	echo -e "${Blue}INSTALL DONE $install_name$None"
	reln $state_run_dir $state_dir/last_ok
	unset state_dir
	unset state_run_dir
	unset install_name
	install_try_push
}

need_state_server(){
	userconfig_state_server=~/userconfig_state
	[[ ! -d $userconfig_state_server ]] && err This is not userconfig state server
	true
}

global_args="$(printf "%q " "$0" "$@")"

if [[ $1 == -v ]]
then
	version(){
		echo $1
		exit 0
	}
fi
if [[ $1 == -t ]]
then
	install_begin(){
		if ${is_sysconfig:-false}
		then
			echo sysconfig
		else
			echo userconfig
		fi
		exit 0
	}
	need_root(){
		true
	}
fi
