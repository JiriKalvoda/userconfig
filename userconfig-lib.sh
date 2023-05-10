cd "$(dirname "$0")"

Red="\e[31m"
Green="\e[32m"
Yellow="\e[33m"
Blue="\e[34m"
Magenta="\e[35m"
None="\e[0m"

USERCONFIG_ROOT="$1"
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

confln()
{
	$USERCONFIG_ROOT/confln "$@"
}

init-service()
{
	$USERCONFIG_ROOT/init-service "$@"
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
		echo "$@"
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
			read in
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
			echo -e " └─   \e[31mRETURN $ret => EXIT\e[0m"
			exit $r
		else
			echo -e " └─   \e[31mRETURN $ret\e[0m"
		fi
	fi
	return $ret
}
