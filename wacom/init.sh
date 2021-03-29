ln -sr wacom-config ~/bin
gcc wacom-daemon.c -o ~/bin/wacom-daemon -pthread
