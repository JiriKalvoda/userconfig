bin=/usr/bin
for i in poweroff reboot
do
	unlink $bin/$i
	echo -e "#!/bin/bash\nsystemctl $i -f  \"\$@\"" > $bin/$i
	chmod +x $bin/$i
done 
