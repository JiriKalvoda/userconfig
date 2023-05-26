# :map \p <HOME>v<END>y:!<c-R>"<BS><CR>
cd ~

# make bin (executable file) directory
mkdir ~/bin

# clone and run userrconfig
git clone https://gitlab.com/JiriKalvoda/userconfig.git
sudo bash userconfig/light/arch.sh
bash userconfig/bash/init.sh
bash userconfig/i3/arch.sh
bash userconfig/vim/arch.sh
bash userconfig/Xresources/arch.sh

# init git username
git config --global user.email "jirikalvoda@kam.mff.cuni.cz"
git config --global user.name "Jiri Kalvoda"

# open urxvt from nemo
gsettings set org.cinnamon.desktop.default-applications.terminal exec terminal
gsettings set org.cinnamon.desktop.default-applications.terminal exec-arg -e 
gsettings set org.gnome.desktop.default-applications.terminal exec terminal
gsettings set org.gnome.desktop.default-applications.terminal exec-arg -e
# org.pwmt.zathura.desktop
