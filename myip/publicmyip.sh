#!/bin/bash

cd ~/.publicmyip

sleepTime=30
. config




while true
do
	echo START
	while true;
	do
		myposition > new
		[[ "$noDownload" == "y" ]] && echo noDownload=$noDownload >> new
		diff new onServer -q >/dev/null
		if [ $? = 0 ]
		then
			echo NO CHANGE
		else
			echo CHANGE: "$(tr '\n' ' ' < new)"
			ssh $user@$server -p$port "cat > $serverDir/$name"  < new
			if [ $? == 0 ]
			then
				mv new onServer
			fi
		fi
		sleep $sleepTime
	done
done

