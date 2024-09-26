systemctl disable --now ModemManager.service
systemctl disable --now avahi-daemon
systemctl disable --now avahi-daemon.socket
systemctl disable --now triggerhappy
systemctl disable --now triggerhappy.socket
systemctl disable --now wpa_supplicant
systemctl disable --now userconfig
systemctl disable --now udisk2
systemctl disable --now udisks2
systemctl disable --now bluetooth
systemctl disable --now wpa_supplicant.service
rm /usr/share/userconf-pi/sshd_banner
rm /etc/ssh/sshd_config.d/rename_user.conf

userdel pi
rm -r /home/pi
