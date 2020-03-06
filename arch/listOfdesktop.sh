for i in *; do if [ $i != mnt ] ; then echo $i; sudo find $i -name "*.desktop" ;fi; done

# use: xdg-mime query default application/pdf  : to detect defalut
# use: xdg-mime default org.pwmt.zathura.desktop application/pdf  : to set defalut
# use: xdg-mime default org.pwmt.zathura.desktop application/pdf  : to set defalut
# update-desktop-database
# xdg-mime query filetype ~/Documents

