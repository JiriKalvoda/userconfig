cd "$(dirname "$0")"

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
	do_eval=false
	while [[ "$1" == "-"* ]]
	do
		if [[ "$1" == "-b" ]]
		then
			do_eval=true
		elif [[ "$1" == "-" ]]
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
