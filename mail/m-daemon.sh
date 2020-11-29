#!/bin/bash

kilrek()
{
	pgrep -P $1 | while read p;
	do
		echo $1 $2 to $p;
		if [[ "$p" != "$2" ]]
		then
			kilrek $p $2
			echo $p;
			kill $p;
		fi
	done

}
whileok()
{
	while true
	do
		sleep 60
		read -ra x < ~/.cm
		delay=$(( $(date +%s) - ${x[0]} ))
		if (( $delay > 120 ))
		then
			(
			echo KILL
			pidwok=$BASHPID
			echo pidwok $pidwok
			kilrek $1 $pidwok
			return;
		)
		fi
	done
}

pid=$BASHPID
while $run
do
	whileok $pid &
	echo -ne "\033]0;MAIL\007"
	osdc --log=2 --color=red "TRY START MAIL"
	m
	sleep 2
done

