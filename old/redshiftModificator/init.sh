if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi
apt install notify-osd
apt install redshift
g++ ./redshiftModificator.c -o /usr/bin/redshiftModificator
chmod u+s /usr/bin/redshiftModificator
g++ ./redshiftModificatorInfo.c -o /usr/bin/redshiftModificatorInfo
chmod u+s /usr/bin/redshiftModificatorInfo
cp ./redshiftModificatorGUI.sh  /usr/bin/redshiftModificatorGUI
chmod o+x         /usr/bin/redshiftModificatorGUI


