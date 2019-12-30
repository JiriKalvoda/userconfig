if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi
apt install numlockx
apt install jq
cp config ~/.config/i3/config 
cp toggle-border ~/.config/i3/i3-toggle-border
