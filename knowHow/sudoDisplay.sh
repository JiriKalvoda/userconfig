  su - $userfirst -c 'xauth list' |\
         grep `echo $DISPLAY |\
             cut -d ':' -f 2 |\
             cut -d '.' -f 1 |\
             sed -e s/^/:/`  |\
         xargs -n 3 xauth add
