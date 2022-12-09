cd "$(dirname "$0")"

USERCONFIG_ROOT="$1"

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

r()
{
	echo "Runnign" 
	print ""$@"
}
