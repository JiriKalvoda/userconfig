if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi
apt install numlockx
cp config ~/.config/i3/config 
