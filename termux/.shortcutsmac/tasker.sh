getNumProc()
{
	# pgrep -f bash" $HOME/.shortcutsmac/tasker.sh" -a 1>&2
	pgrep -f bash" $HOME/.shortcutsmac/tasker.sh" | wc -l
}

i=0
procNum=$(getNumProc)
while [[ $procNum -gt 2 ]]
do
	i=$((i+1))
	[[ $i -ge $((100 + $RANDOM % 10)) ]] && exit 100
	#echo $procNum
	procNum=$(getNumProc)
	sleep 0.1
done
echo RUN $procNum
sshd

datadir=/storage/emulated/0/termux/tasker
cpdir=$HOME/.tasker
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


for i in $(ls)
do
	if [[ -f $i/run ]]
	then
		[[ -d $cpdir/$i ]] && rm $cpdir/$i -r
		mv $i $cpdir/$i
		chmod +x $cpdir/$i/run
		ssh localhost -p8022 bash -c "\"cd $cpdir/$i;ls;./run;cd ..; rm $cpdir/$i -r:\"" &
	fi
done
