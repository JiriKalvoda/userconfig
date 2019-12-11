if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi
rm /usr/share/vim/vimrc
rm /usr/share/vim/basicFile.cpp
cp vimrc /usr/share/vim/
cp basicFile.cpp /usr/share/vim/
