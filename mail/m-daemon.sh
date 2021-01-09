#!/bin/bash

kilrek()
{
	if (( $3 > 0 ));
	then
		pgrep -P $1 | while read p;
		do
			# echo $1 $2 to $p;
			if [[ "$p" != "$2" ]]
			then
				kilrek $p $2 $(( $3 - 1 ))
				# echo $p;
				kill $p;
			fi
		done
	fi

}
whileok()
{
	(
	while true
	do
		sleep 60
		read -ra x < ~/.cm
		delay=$(( $(date +%s) - ${x[0]} ))
		if (( $delay > 120 ))
		then
			# echo KILL
			pidwok=$BASHPID
			# echo pidwok $pidwok
			kilrek $1 $pidwok 5
			return;
		fi
	done
)
}

pid=$BASHPID
while $run
do
	whileok $pid &
	echo -ne "\033]0;MAIL\007"
	osdc --log=2 --color=red "TRY START MAIL"
	startTime=$(date +%s)
	m
	timer=$(( $(date +%s) - $startTime )) 
	if (( timer < 60 ))
	then
		echo STOP, BUT WAITING
		sleep $(( 60 - timer ))
	fi
	(
		pidwok=$BASHPID
		kilrek $pid $pidwok 5
	)
	sleep 2
done

