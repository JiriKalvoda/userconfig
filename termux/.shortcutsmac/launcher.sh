datadir=/storage/emulated/0/termux/launcher
cpdir=$HOME/.launcher
cd $datadir
for i in $(ls)
do
	j=${i/-/\/}
	# echo $i $j
	if [[ "$i" != "$j" ]]
	then
		mkdir -p $(dirname $j)
		mv $i $j
	fi
done


sshd

for i in $(ls)
do
	if [[ -f $i/run ]]
	then
			[[ -d $cpdir/$i ]] && rm $cpdir/$i -r
		mv $i $cpdir/$i
		if [[ $? == 0 ]]
		then
			# echo I $i
			[[ "$(ls)" != "" ]] && launcher
			cd $cpdir/$i;
			chmod +x $cpdir/$i/run
			ssh localhost -p 8022 -t bash -c "\"export -n SSH_CONNECTION ; $cpdir/$i/run \""
			rm $cpdir/$i -r
			exit 0
		fi
	fi
done
