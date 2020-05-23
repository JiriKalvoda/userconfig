#! /bin/bash
set -m
kilrek()
{
	pgrep -P $1 | while read p;
	do
		kilrek $p;
		#echo $p;
		kill $p;
	done

}
wdel()
{
		#echo START WDEL | lolcat
		#echo $2 $3 $$ 
while true;
do
	sleep 0.02
	run="$(cat $1 2>/dev/null)";
	#echo run:$run
	if [ "$run" != "" ]
	then
		break;
	fi
	kill -0 $2 2>/dev/null
	if [[ $? = 1 ]]
	then
		#echo NO PROCES  BREAK | lolcat
		break;
	fi
	kill -0 $3 2>/dev/null
	if [[ $? = 1 ]]
	then
		#echo NO MAIN PROCES  BREAK | lolcat
		break;
	fi
done
		#echo BREAK WDEL | lolcat
		kilrek $2
#echo $(ps -s $2 -o pid=)
#kill $(ps -s $2 -o pid=)
#echo kill  -TERM -$2
#kill  -TERM -$2
}
i=-1;
lastBash=0;
mainProces=$2;
if [ "$2" = "" ]
then
	mainProces=$$
fi
while true;
do
	run="$(cat $1 2>/dev/null)";
	if [ "$run" != "" ]
	then
		#echo START | lolcat
		#sleep 0.1
		rm $1
		lastBash=0;
	else
		run="bash"
		if [ $lastBash = 1 ]
		then
			exit 0
		fi
		lastBash=1;
	fi
	kill -0 $2 2>/dev/null
	if [[ $? = 1 ]]
	then
		#echo NO PROCES  BREAK | lolcat
		break;
	fi
	i=$(( i  + 1))
	#echo  run X$run X
	(ISBREAKEBLE=1  bash -c "sleep 0.1;$run" ) &
	p=$!
	sleep 0.0001
	#echo $p $$
	#(sleep 2; pkill -P $p ) &
	wdel $1 $p $mainProces &
	fg $(( 2 * i + 1 )) 1>/dev/null
done
