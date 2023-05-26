adate="date +%Y-%m-%d___%H:%M:%S"
$adate
sudo date -s "$(wget -qSO- --max-redirect=0 kam.mff.cuni.cz 2>&1 | grep Date: | cut -d' ' -f5-8)Z"
sudo  hwclock --systohc
$adate
