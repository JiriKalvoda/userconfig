#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

../git-clupdate git://git.ucw.cz/teatimer.git build_git
r -b "cd build_git ; make"
confln build_git/teatimer ~/bin/
confln tt ~/bin/

install_ok
