#!/bin/bash
cd "$(dirname "$0")"

../git-clupdate git://git.ucw.cz/teatimer.git build_git
(cd build_git ; make)
confln build_git/teatimer ~/bin/
confln tt ~/bin/
