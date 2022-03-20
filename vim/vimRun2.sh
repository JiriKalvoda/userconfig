exec 3<>$1

killrek()
{
	# $1 -- actual proces
	# $2 -- no not kill pid
	# $3 -- kill actual if is 1
	echo kilrek 1:$1 2:$2 3:$3
	if [[ $1 == "" ]]
	then
		echo EMPTY
		exit
	fi
	if [[ $1 == "$2" ]]
	then
		echo NOPE
		exit
	fi
	pq=$(pgrep -P "$1")
	if [[ $3 == 1 ]]
	then
		kill $1
	fi
	echo -n "$pg" | while read p
	do
		echo "pg:$pg p:$p"
		killrek "$p" "$2" 1
	done
	echo ENDrek $1
}
waiter()
{
	# $1 -- main proces pid
	if ! read -u 3 cmd
	then
		echo end waiter
	fi
	echo kill
	echo "$cmd" >&3
	killrek $1 $BASHPID 0
	exit 0
}


while true
do
	if ! read -u 3 cmd
	then
		echo end
		exit 0
	fi
	p=$BASHPID
	(waiter $p )&
	bash -c "$cmd"
done
