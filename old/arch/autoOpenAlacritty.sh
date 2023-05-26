sudo ln -s /usr/bin/alacritty /usr/bin/terminal


aurman -S xdg-utils-terminal-true-git
#sudo ln -s /usr/bin/urxvt /usr/bin/$TERM
sudo sed -i '1 a TERM=terminal' /usr/bin/xdg-terminal



gsettings set org.cinnamon.desktop.default-applications.terminal exec teminal
gsettings set org.cinnamon.desktop.default-applications.terminal exec-arg -e
